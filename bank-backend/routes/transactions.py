from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Transaction, Account
from src.auth import get_current_user
from pydantic import BaseModel

from routes.aml import send_transaction_to_aml
from src.celery_app import celery_app, process_aml_check

router = APIRouter()


# Define the transfer model
class TransferRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float

@router.post("/transfer")
def create_transfer(transfer_data: TransferRequest, db: Session = Depends(get_db),
                    user_id: int = Depends(get_current_user)):
    """
    Transfer funds from one account to another
    :param transfer_data: sender id, receiver id, amount
    :param db: database session
    :param user_id: logged-in user id
    :return: information about successful transfer
    """
    sender_account = transfer_data.sender_account
    receiver_account = transfer_data.receiver_account
    amount = transfer_data.amount
    celery_app.send_task("create_transaction", args=[user_id, sender_account, receiver_account, amount])

    return {"message": "Transaction queued."}

@router.post("/transfer/accept")
def transfer_accept(data: dict, db: Session = Depends(get_db)):
    transaction_id = data["transaction_id"]
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    db.commit()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    sender_account = db.query(Account).filter(Account.id == transaction.from_account_id).first()
    sender_account.balance -= transaction.amount
    if transaction.to_account_id:
        receiver_account=db.query(Account).filter(Account.id == transaction.to_account_id).first()
        receiver_account.balance += transaction.amount

    transaction.status = "completed"

    db.commit()
    db.refresh(transaction)
    db.refresh(sender_account)
