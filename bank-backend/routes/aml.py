import redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth import aml_required, hash_password
from src.database import get_db
from src.models import User, Account, AtmDevice, Transaction, AmlToControl
import random
from pydantic import BaseModel, constr
from typing import Optional, List


from datetime import datetime, timedelta, timezone
import pytz
import httpx

class TransactionAction(BaseModel):
    id: int

router = APIRouter()
r = redis.Redis(host='localhost', port=6379, db=0)

@router.get("/aml/transactions")
def get_transactions(db: Session = Depends(get_db), current_user=Depends(aml_required)):
    """Zwraca listę transakcji dla administratora"""

    transactions = db.query(Transaction).filter_by(status='aml_blocked').all()

    list_reasoning=[]
    for transaction in transactions:
        reason=db.query(AmlToControl).filter_by(transaction_id=transaction.id).all()
        list_reasoning.append(reason)

        ##TODO: dodać do frontu wykorzystanie list_reasoning aby wyświetlać w aml_dashboard jaki powód
        ## [Konrad] Proponuję endpoint jak niżej:

    return transactions

@router.get("/aml/reason")
def get_reason(id: int, db: Session = Depends(get_db), current_user=Depends(aml_required)):
    """Zwraca listę powodów podejrzeń"""
    tx = db.query(Transaction).filter(Transaction.id == id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    reason = db.query(AmlToControl).filter_by(transaction_id=id).first()
    if not reason:
        raise HTTPException(status_code=404, detail="Reason not found")
    return reason

@router.post("/aml/accept")
def accept_transaction(transaction: TransactionAction, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    ## moved the acceptance to next endpoint, to keep it consistent
    send_transaction_to_accept(transaction.id)

    return {"message": "Transaction accepted"}


@router.post("/aml/reject")
def reject_transaction(transaction: TransactionAction, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.status = "failed"
    db.commit()
    return {"message": "Transaction rejected"}

@router.post("/aml/check")
def check_transaction(data: dict, db: Session = Depends(get_db)):
    transaction_id = data["transaction_id"]


    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    transaction.status="aml_processed"
    db.commit()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")


    problems_found=[]

    ## checking what kind of transaction is being tested:
    if transaction.type == "deposit":
        pass
    elif transaction.type == "withdrawal":
        pass

    elif transaction.type == "transfer":

        ## suspicious ammount of transferred money:
        if is_large_transaction(transaction.amount):
            problems_found.append("is_large_transaction")

        ## too many transactions in a short term (ex. 1 min, 5 transfers)
        if is_rapid_transactions(db, transaction.from_account_id):
            problems_found.append("is_rapid_transactions")

        # TODO: strange time of transfer <-- to be

        ## analysis of user's profile --> "does the user act as usually?"
        if is_unusual_amount(db, transaction.from_account_id, transaction.amount):
            transaction.status = "aml_blocked"
            problems_found.append("is_unusual_amount")

        if is_unusual_frequency(db, transaction.from_account_id):
            problems_found.append("is_unusual_frequency")


    else:
        raise HTTPException(status_code=405, detail="Transaction error: wrong transaction type")


    if problems_found:
        transaction.status = "aml_blocked"
        aml_transaction=AmlToControl(transaction_id=transaction.id,reasoning=",".join(problems_found))
        db.add(aml_transaction)
    else:
        transaction.status = "aml_approved"
        send_transaction_to_accept(transaction.id)

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


def send_transaction_to_accept(transaction_id: int):
    transaction_accept="http://localhost:8000/transfer/accept"
    data={"transaction_id": transaction_id}
    try:
        response = httpx.post(transaction_accept, json=data)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send to the acceptance module {exc}")


def is_large_transaction(amount: float, threshold: float = 10000) -> bool:
    return amount > threshold



def is_rapid_transactions(db, account_id: int, threshold: int = 5, time_to_compare: int = 1) -> bool:
    time_now = datetime.now(pytz.timezone('Europe/Warsaw'))
    comparing_date = time_now - timedelta(minutes=time_to_compare)


    count = db.query(Transaction).filter(
        Transaction.from_account_id == account_id,
        Transaction.date >= comparing_date  # Porównanie daty z bazy z datą w strefie warszawskiej
    ).count()

    return count > threshold

def is_unusual_amount(db: Session, account_id: int, amount: float, threshold: float = 3.0) -> bool:
    transactions = db.query(Transaction).filter(
        Transaction.from_account_id == account_id,
        Transaction.amount > 0
    ).all()

    amounts = [t.amount for t in transactions]

    if len(amounts) < 5: #not enough data
        return False

    avg = sum(amounts) / len(amounts)
    std_dev = (sum((x - avg) ** 2 for x in amounts) / len(amounts)) ** 0.5

    return amount > avg + threshold * std_dev #current comparison --> is the amount bigger than std_dev * threshold


def is_unusual_frequency(db: Session, account_id: int, recent_days: int = 7, factor_threshold: float = 2.0) -> bool:
    now = datetime.now(pytz.timezone("Europe/Warsaw"))
    recent_start = now - timedelta(days=recent_days)
    earlier_start = recent_start - timedelta(days=30)

    # Transactions from previous 7 days
    recent_count = db.query(Transaction).filter(
        Transaction.from_account_id == account_id,
        Transaction.date >= recent_start
    ).count()

    # Transactions from previous 7 days (previous 30 days)
    past_transactions = db.query(Transaction).filter(
        Transaction.from_account_id == account_id,
        Transaction.date >= earlier_start,
        Transaction.date < recent_start
    ).all()

    past_days = 30
    past_avg = len(past_transactions) / past_days if past_days else 0

    recent_avg = recent_count / recent_days

    return past_avg > 0 and (recent_avg > factor_threshold * past_avg)
