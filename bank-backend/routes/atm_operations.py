from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Transaction, Account, Card, AtmDevice, User
from pydantic import BaseModel
from datetime import datetime, timezone
import requests
from routes.verify import router as verify_router

router = APIRouter()
router.include_router(verify_router)


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

    # Wybranie dostępnych bankomatów z tabeli
    atm_active = db.query(AtmDevice).filter(AtmDevice.status == 'active').first()
    if not atm_active:
        raise HTTPException(status_code=404, detail="Brak dostępnych bankomatów.")

    return {"atm_id": atm_active.id}


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
    if atm_data.status == 'busy':
        raise HTTPException(status_code=409, detail="Bankomat jest zajęty.")

    # Bankomat zostaje oznaczony jak zajęty
    atm_data.status = 'busy'
    db.commit()
    db.refresh(atm_data)

    # Sprawdzenie, czy karta może być obsłużona przez bankomat
    card_data = db.query(Card).filter(Card.id == card_id).first()
    if not card_data:

        atm_data.status = 'active'
        db.commit()
        db.refresh(atm_data)
        raise HTTPException(status_code=404, detail="Nie rozpoznano karty.")

    return {"status": "ok"}


@router.post("/pin-verification")
def verify_pin(verification_data: PINVerificationModel, db: Session = Depends(get_db)):

    # Weryfikacja pinu i klienta

    card_id = verification_data.card_id
    pin = verification_data.pin

    card_data = db.query(Card).filter(Card.id == card_id).first()

    # Sprawdzenie PIN-u podanego przez klienta (czy PIN pasuje do karty)
    pin_data = db.query(Card).filter(Card.id == card_id, Card.pin == pin).first()
    if not pin_data:
        raise HTTPException(status_code=401, detail="Wprowadzony PIN jest niepoprawny.")

    # Sprawdzenie, czy konto może być obsłużone (czy istnieje oraz, czy nie jest zablokowane)
    # Sprawdzenie, czy użytkownik nie jest tymczasowo zablokowany
    account_data = db.query(Account).filter(Account.id == card_data.account_id).first()
    # user_data = db.query(User).filter(User.id == account_data.user_id).first()
    if not account_data:
        raise HTTPException(status_code=404, detail="Nie rozpoznano konta.")

    if account_data.status == 'busy':
        raise HTTPException(status_code=403, detail="Usługa tymczasowo niedostępna.")

    # if user_data.status == 'disabled':
    #    raise HTTPException(status_code=403, detail="Usługa tymczasowo niedostępna.")

    account_data.status = 'busy'
    db.commit()
    db.refresh(account_data)

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

    atm_data = db.query(AtmDevice).filter(AtmDevice.id == atm_id).first()
    card_data = db.query(Card).filter(Card.id == card_id).first()
    account_data = db.query(Account).filter(Account.id == card_data.account_id).first()

    # Sprawdzenie, czy na koncie są wystarczające środki
    if account_data.balance < amount:
        raise HTTPException(status_code=409, detail="Niewystarczające środki.")

    # Sprawdzenie, czy podaną kwotę można wypłacić
    if amount % 10 != 0:
        raise HTTPException(status_code=409, detail="Bankomat nie może wydać żądanej kwoty.")

    # Zablokowanie możliwości wykonywania innych operacji na koncie
    account_data.status = 'busy'
    db.commit()
    db.refresh(account_data)

    # Nowy rekord transakcji
    new_transaction = Transaction(from_account_id=account_data.id, to_account_id=0, amount=amount,
                                  type='withdrawal', date=datetime.now(), status='pending', device_id=atm_id)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    # Weryfikacja
    verification_payload = {
        "transaction_id": new_transaction.id,
    }
    verification_response = requests.post("http://localhost:8000/verify-transaction-auto", json=verification_payload)

    # Jeżeli zwrócono kod błędu — transakcja odrzucona
    if verification_response.status_code != 200:
        new_transaction.status = 'failed'
        new_transaction.date = datetime.now()
        db.commit()  # Aktualizacja informacji w bazie
        db.refresh(new_transaction)

        return {"message": "Operacja odrzucona! Spróbuj ponownie później.", "status": "failure",
                "transaction_id": new_transaction.id}

    # Jeżeli zwrócono completed — można finalizować transakcję
    elif verification_response.json()['status'] == 'completed':

        new_transaction.status = 'completed'
        new_transaction.date = datetime.now()
        account_data.balance -= amount
        db.commit()  # Aktualizacja informacji w bazie
        db.refresh(new_transaction)

        return {"message": "Operacja zakończona powodzeniem!", "status": "success",
                "transaction_id": new_transaction.id}


    # Jeśli weryfikacja się nie powiodła — transakcja wciąż oczekuje na ręczne zatwierdzenie
    else:
        new_transaction.status = 'pending'
        new_transaction.date = datetime.now()
        db.commit()  # Aktualizacja informacji w bazie
        db.refresh(new_transaction)

        return {"message": "Operacja odrzucona! Na twoim koncie wykryto podejrzaną aktywność."
                           "Skontaktuj się z oddziałem banku.", "status": "pending",
                "transaction_id": new_transaction.id}


@router.get("/atm-operation/confirmation")
def get_confirmation(transaction_id: int, db: Session = Depends(get_db)):

    # Przygotowanie potwierdzenia

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if transaction:
        confirmation_txt = f"Data: {transaction.date}\nKwota: {transaction.amount}\nStatus: {transaction.status}"

        return {"confirmation": confirmation_txt}

    else:
        # ewentualnie raise error tutaj
        return {"confirmation": "Błąd pobierania danych."}
