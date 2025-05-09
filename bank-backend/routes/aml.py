import redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth import aml_required, hash_password
from src.database import get_db
from src.models import User, Account, AtmDevice, Transaction
import random
from pydantic import BaseModel, constr
from typing import Optional, List

import time
from datetime import datetime, timedelta, timezone
import httpx


router = APIRouter()
r = redis.Redis(host='localhost', port=6379, db=0)

@router.post("/aml/check")
def check_transaction(data: dict, db: Session = Depends(get_db)):
    transaction_id = data["transaction_id"]
    amount = data["amount"]

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    db.commit()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    ## checking what kind of transaction is being tested:
    if transaction.type == "deposit":
        pass
    elif transaction.type == "withdrawal":
        pass

    elif transaction.type == "transfer":


        ## suspicious ammount:
        if is_large_transaction(transaction.amount):
            transaction.status = "aml_blocked"
            print(f"Transaction {transaction_id} is suspicious!")

        ## too many transactions in a short term (ex. 1 min, 5 transfers)

        elif is_rapid_transactions(db, transaction.id):
            transaction.status = "aml_blocked"
            print(f"Transaction {transaction_id} is suspicious!")

        ## strange time of transfer

        ## analysis of user's profile

        ##
        else:
            transaction.status = "aml_approved"
            print(f"Transaction {transaction_id} is normal.")





    else:
        raise HTTPException(status_code=405, detail="Transaction error: wrong transaction type")

    #simulation of changing statuses
    time.sleep(10)
    db.commit()

    return {"status": "checked", "new_status": transaction.status}



## func used
def send_transaction_to_aml(transaction_id: int, amount: float):
    aml_url = "http://localhost:8000/aml/check"

    data = {
        "transaction_id": transaction_id,
        "amount": amount,
    }

    try:
        response = httpx.post(aml_url, json=data)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to notify AML service: {exc}")

def is_large_transaction(amount: float, threshold: float = 10000) -> bool:
    return amount > threshold



def is_rapid_transactions(db, account_id: int, threshold: int = 5) -> bool:
    """
    Sprawdza, czy liczba transakcji z danego konta w ciągu ostatnich 5 minut przekracza określony próg.

    :param db: sesja bazy danych
    :param account_id: ID konta nadawcy (from_account_id)
    :param threshold: maksymalna liczba transakcji w oknie 5 minut
    :return: True jeśli liczba transakcji przekracza próg
    """
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

    count = db.query(Transaction).filter(
        Transaction.from_account_id == account_id,
        Transaction.date >= five_minutes_ago
    ).count()

    return count > threshold
