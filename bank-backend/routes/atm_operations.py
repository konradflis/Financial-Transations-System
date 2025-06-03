from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Transaction, Account, Card, AtmDevice, User
from pydantic import BaseModel
from datetime import datetime, timezone
import requests
from routes.verify import router as verify_router
import pytz
import time
from redlock import Redlock

from src.celery_app import process_atm_operation_task
from src.celery_app import celery_app
router = APIRouter()
router.include_router(verify_router)

redlock = Redlock([{"host": "redis", "port": 6379}])


class AtmFreeRequest(BaseModel):
    atm_id: int


class AccountFreeRequest(BaseModel):
    account_id: int


# Model weryfikacji urządzenia
class ATMVerificationModel(BaseModel):
    card_id: int
    atm_id: int


# Model weryfikacji klienta
class PINVerificationModel(BaseModel):
    card_id: int
    pin: str


# Model operacji w bankomacie
class ATMOperationModelPIN(BaseModel):
    card_id: int
    atm_id: int
    amount: float


# Model żądania potwierdzenia
class ConfirmationRequest(BaseModel):
    transaction_id: int


@router.get("/atm-assignment")
def assign_atm(db: Session = Depends(get_db)):

    # Oczekiwanie na odpowiedź workera
    response = assign_atm_intervals()
    if response['status'] != 'success':
        raise HTTPException(status_code=404, detail="Brak dostępnych bankomatów.")

    return {"atm_id": response['atm_id']}


@router.post("/atm-free")
def free_atm(atm_request: AtmFreeRequest, db: Session = Depends(get_db)):

    # Zwolnienie bankomatu przy anulowaniu operacji
    atm_id = atm_request.atm_id
    atm_data = db.query(AtmDevice).filter(AtmDevice.id == atm_id).first()
    if not atm_data:
        raise HTTPException(status_code=404, detail="Bankomat nie istnieje.")

    atm_data.status = 'active'
    db.commit()
    db.refresh(atm_data)

    return {"message": "ok"}


@router.post("/account-free")
def free_account(account_request: AccountFreeRequest, db: Session = Depends(get_db)):

    # Zwolnienie konta przy anulowaniu operacji
    account_id = account_request.account_id
    account_data = db.query(Account).filter(Account.id == account_id).first()
    if not account_data:
        raise HTTPException(status_code=404, detail="Nie rozpoznano konta.")

    account_data.status = 'active'
    db.commit()
    db.refresh(account_data)

    return {"message": "ok"}


@router.post("/atm-operation/verification")
def verify_atm_operation(operation_data: ATMVerificationModel, db: Session = Depends(get_db)):

    """
    Weryfikacja warunków do przeprowadzenia operacji w bankomacie, tj. czy karta i bankomat "działają".
    :param operation_data:
    :param db:
    :return:
    """

    print("Received operation data:", operation_data)

    card_id = operation_data.card_id
    atm_id = operation_data.atm_id

    # Sprawdzenie, czy bankomat istnieje
    atm_data = db.query(AtmDevice).filter(AtmDevice.id == atm_id).first()
    if not atm_data:
        raise HTTPException(status_code=404, detail="Bankomat nie istnieje.")

    # Sprawdzenie, czy bankomat jest wolny — czy może wykonać teraz operację
    # BANKOMANT JEST JUŻ ZAREZERWOWANY DLA KLIENTA NA POCZĄTKU ENDPOINTA

    # Sprawdzenie, czy karta może być obsłużona przez bankomat
    card_data = db.query(Card).filter(Card.id == card_id).first()
    if not card_data:

        atm_data.status = 'active'
        db.commit()
        db.refresh(atm_data)
        raise HTTPException(status_code=404, detail="Nie rozpoznano karty.")

    return {"status": "ok"}


@router.post("/atm-operation/pin-verification")
def verify_pin(verification_data: PINVerificationModel, db: Session = Depends(get_db)):

    # Weryfikacja pinu i klienta

    card_id = verification_data.card_id
    pin = verification_data.pin

    #card_data = db.query(Card).filter(Card.id == card_id).first()

    # Sprawdzenie PIN-u podanego przez klienta (czy PIN pasuje do karty)
    pin_data = db.query(Card).filter(Card.id == card_id, Card.pin == pin).first()
    if not pin_data:
        raise HTTPException(status_code=401, detail="Wprowadzony PIN jest niepoprawny.")

    # Sprawdzenie, czy konto może być obsłużone (czy istnieje oraz, czy nie jest zablokowane)
    # Sprawdzenie, czy użytkownik nie jest tymczasowo zablokowany
    # Oczekiwanie na uzyskanie dostępu do konta
    response = check_account_lock(card_id)

    if response['label'] == 'timeout':
        raise HTTPException(status_code=404, detail="Nie znaleziono konta.")
    elif response['label'] == 'account_busy' or response['label'] == 'user_disabled':
        raise HTTPException(status_code=403, detail="Usługa tymczasowo niedostępna.")
    else:
        return {"message": "ok"}


@router.post("/atm-operation/withdrawal")
def withdraw_funds(withdrawal_data: ATMOperationModelPIN, db: Session = Depends(get_db)):

    """
    Dalsza weryfikacja -- po wprowadzeniu PIN oraz wykonanie wypłaty.
    :param withdrawal_data:
    :param db:
    :return:
    """
    card_id = withdrawal_data.card_id
    atm_id = withdrawal_data.atm_id
    amount = withdrawal_data.amount

    card_data = db.query(Card).filter(Card.id == card_id).first()
    account_data = db.query(Account).filter(Account.id == card_data.account_id).first()

    # Sprawdzenie, czy na koncie są wystarczające środki
    if account_data.balance < amount:
        raise HTTPException(status_code=409, detail="Niewystarczające środki.")

    # Sprawdzenie, czy podaną kwotę można wypłacić
    if amount % 10 != 0:
        raise HTTPException(status_code=409, detail="Bankomat nie może wydać żądanej kwoty.")

    # Nowy rekord transakcji
    new_transaction = Transaction(from_account_id=account_data.id, to_account_id=0, amount=amount,
                                  type='withdrawal', status='pending', device_id=atm_id)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    celery_app.send_task("process_atm_operation_task", args=[new_transaction.id])

    return {
        "message": "Transakcja w toku...",
        "transaction_id": new_transaction.id,
        "status": "processing"
    }


@router.post("/atm-operation/deposit")
def deposit_funds(deposit_data: ATMOperationModelPIN, db: Session = Depends(get_db)):

    """
    Dalsza weryfikacja -- po wprowadzeniu PIN oraz wykonanie wypłaty.
    :param deposit_data:
    :param db:
    :return:
    """

    card_id = deposit_data.card_id
    atm_id = deposit_data.atm_id
    amount = deposit_data.amount

    card_data = db.query(Card).filter(Card.id == card_id).first()
    account_data = db.query(Account).filter(Account.id == card_data.account_id).first()

    # Sprawdzenie, czy podaną kwotę można wpłacić
    if amount % 10 != 0:
        raise HTTPException(status_code=409, detail="Bankomat nie może przyjąć żądanej kwoty.")

    # Nowy rekord transakcji
    new_transaction = Transaction(from_account_id=0, to_account_id=account_data.id, amount=amount,
                                  type='deposit', status='pending', device_id=atm_id)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    celery_app.send_task("process_atm_operation_task", args=[new_transaction.id])

    return {
            "message": "Transakcja w toku...",
            "transaction_id": new_transaction.id,
            "status": "processing"
        }

@router.get("/atm-operation/confirmation")
def get_confirmation(transaction_id: int, db: Session = Depends(get_db)):

    # Przygotowanie potwierdzenia
    time.sleep(1)
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if transaction:

        if transaction.type == 'withdrawal':
            type = 'wypłata'
        elif transaction.type == 'deposit':
            type = 'wpłata'
        else:
            type = 'przelew'

        if transaction.status == 'pending':
            status = 'oczekująca\n-- SKONTAKTUJ SIĘ Z ODDZIAŁEM BANKU --'
        elif transaction.status == 'completed':
            status = 'sukces'
        else:
            status = 'niepowodzenie'

        confirmation_txt = f"Data: {transaction.date.strftime('%Y-%m-%d %H:%M:%S')}\nTyp: {type}\nKwota: {transaction.amount} PLN\nStatus operacji: {status}"

        return {"confirmation": confirmation_txt}

    else:
        # ewentualnie raise error tutaj
        return {"confirmation": "Błąd pobierania danych."}


def assign_atm_intervals(timeout=10, interval=2):

    """
    Próba przypisania bankomatu przez [timeout] sekund.
    :param timeout: jak długo próbować
    :param interval: co ile wysyłać ponowną próbę
    :return:
    """

    db = next(get_db())
    waited = 0

    # Zapytanie
    try:
        while waited < timeout:

            # Przypisanie bankomatu do użytkownika — oznaczenie go jako zajęty
            atm_chosen = db.query(AtmDevice).filter(AtmDevice.status == 'active').with_for_update().first()
            if atm_chosen:
                atm_chosen.status = 'busy'
                db.commit()
                return {"status": "success", "atm_id": atm_chosen.id}

            time.sleep(interval)    # Odczekaj odpowiednią ilość sekund
            waited += interval
            db.rollback()           # odświeżenie
        return {"status": "failure", "error_message": "Brak dostępnych bankomatów. Spróbuj ponownie później."}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Nieoczekiwany błąd: {e}"}
    finally:
        db.close()


def check_account_lock(card_id: int):

    """
    Próba uzyskania dostępu do konta.
    :param card_id: karta połączona z kontem
    :return:
    """

    db = next(get_db())
    lock = None

    try:
        card = db.query(Card).filter(Card.id == card_id).first()
        if not card:
            return {"status": "error", "message": "Nie znaleziono karty"}

        account = db.query(Account).filter(Account.id == card.account_id).first()
        user = db.query(User).filter(User.id == account.user_id).first()

        lock_key = f"lock-account-{account.id}"
        for _ in range(10):  # Próba uzyskania dostępu do konta (lock_key) przez 10 sekund
            lock = redlock.lock(lock_key, 10000)  # zablokowanie dostępu innym procesom na 10 sekund
            if lock:
                break
            time.sleep(1)

        if not lock:        # nie udało się uzyskać dostępu
            return {"status": "error", "label": "timeout"}

        if account.status == 'busy':       # udało się uzyskać dostęp, ale konto jest wciąż zajęte
            return {"status": "error", "label": "account_busy"}

        if user.status == 'disabled':       # klient jest zablokowany
            return {"status": "error", "label": "user_disabled"}

        account.status = 'busy'
        db.commit()
        db.refresh(account)

        return {"status": "success", "account_id": account.id, 'label': 'success'}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Nieoczekiwany błąd: {e}"}

    finally:
        if lock:
            redlock.unlock(lock)
        db.close()