from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Transaction, Account, Card, AtmDevice, User
from pydantic import BaseModel
from datetime import datetime
import requests

router = APIRouter()


# Model operacji w bankomacie
class ATMOperationModel(BaseModel):
    card_id: int
    atm_id: int
    amount: float


@router.post("/withdrawal")
def withdraw_funds(withdrawal_data: ATMOperationModel, db: Session = Depends(get_db),
                   pin: str = Form(...), confirmation: bool = Query(False)):

    card_id = withdrawal_data.card_id
    atm_id = withdrawal_data.atm_id
    amount = withdrawal_data.amount

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

    # Sprawdzenie, czy karta może być obsłużona przez bankomat
    card_data = db.query(Card).filter(Card.id == card_id).first()
    if not card_data:
        raise HTTPException(status_code=404, detail="Nie rozpoznano karty.")

    # Sprawdzenie PIN-u podanego przez klienta (czy PIN pasuje do karty)
    pin_data = db.query(Card).filter(Card.id == card_id, Card.pin == pin).first()
    if not pin_data:
        raise HTTPException(status_code=401, detail="Wprowadzony PIN jest niepoprawny.")

    # Sprawdzenie, czy konto może być obsłużone (czy istnieje oraz, czy nie jest zablokowane)
    # Sprawdzenie, czy użytkownik nie jest tymczasowo zablokowany
    account_data = db.query(Account).filter(Account.id == card_data.account_id).first()
    user_data = db.query(User).filter(User.id == account_data.user_id).first()
    if not account_data:
        raise HTTPException(status_code=404, detail="Nie rozpoznano konta.")

    if account_data.status == 'busy':
        raise HTTPException(status_code=403, detail="Usługa tymczasowo niedostępna.")

    #if user_data.status == 'disabled':
    #    raise HTTPException(status_code=403, detail="Usługa tymczasowo niedostępna.")

    # Sprawdzenie, czy na koncie są wystarczające środki
    if account_data.balance < amount:
        raise HTTPException(status_code=409, detail="Niewystarczające środki.")

    # Sprawdzenie, czy podaną kwotę można wypłacić
    if amount % 10 != 0:
        raise HTTPException(status_code=409, detail="Bankomat nie może wydać żądanej kwoty.")

    # Zablokowanie możliwości wykonywania innych operacji na koncie
    account_data.status = 'busy'
    db.commit()

    # Nowy rekord transakcji
    new_transaction = Transaction(from_account_id=account_data.id, to_account_id=None, amount=amount,
                                  transaction_type='withdrawal', date=datetime.now(), status='pending', device_id=atm_id)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    # Weryfikacja
    verification_payload = {
        "transaction_id": new_transaction.id,
        "account_id": new_transaction.from_account_id,
        "to_account_id": new_transaction.to_account_id,
        "amount": new_transaction.amount,
        "transaction_type": new_transaction.type,
        "date": new_transaction.date,
        "status": new_transaction.status,
        "device_id": new_transaction.device_id
    }
    verification_response = requests.post("http://localhost:8000/verify-transaction-auto", json=verification_payload)

    # Jeżeli zwrócono kod błędu — transakcja odrzucona
    if verification_response.status_code != 200:
        new_transaction.transaction_status = 'failed'
        db.commit()  # Aktualizacja informacji w bazie

        return {"message": "Operacja odrzucona! Spróbuj ponownie później."}

    # Jeżeli zwrócono completed — można finalizować transakcję
    elif verification_response.json()['status'] == 'completed':

        new_transaction.transaction_status = 'completed'
        account_data.balance -= amount
        account_data.status = 'active'
        atm_data.status = 'active'
        db.commit()  # Aktualizacja informacji w bazie

        # Ewentualne wydrukowanie potwierdzenia
        if confirmation:
            confirmation_txt = f"Date: {new_transaction.date}, amount: {new_transaction.amount} via atm {atm_id}."

            return {"message": "Withdrawal finished successfully!", "confirmation": confirmation_txt}

        else:
            return {"message": "Withdrawal finished successfully!"}

    # Jeśli weryfikacja się nie powiodła — transakcja odrzucona
    else:
        new_transaction.transaction_status = 'failed'
        db.commit()  # Aktualizacja informacji w bazie

        return {"message": "Operacja odrzucona! Na twoim koncie wykryto podejrzaną aktywność."
                           "Skontaktuj się z oddziałem banku."}



