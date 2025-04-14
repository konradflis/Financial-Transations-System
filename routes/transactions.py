from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Transaction, Account
from src.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


# Define the transfer model
class TransferRequest(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float


@router.post("/transfer")
def create_transfer(transfer_data: TransferRequest, db: Session = Depends(get_db),
                    user_id: int = Depends(get_current_user)):
    """
    Transfer funds from one account to another
    :param transfer_data: sender id, receiver id, amount
    :param db: database session
    :param user_id: logged-in user id
    :return: information about successful transer
    """

    sender_id = transfer_data.sender_id
    receiver_id = transfer_data.receiver_id
    amount = transfer_data.amount

    # Raise the exception when sender account is not the user's account
    sender_account = db.query(Account).filter(Account.id == sender_id, Account.user_id == user_id).first()
    if not sender_account:
        raise HTTPException(status_code=403, detail="You can only send money from your own account.")

    # Raise the exception when receiver account is not found
    receiver_account = db.query(Account).filter(Account.id == receiver_id).first()
    if not receiver_account:
        raise HTTPException(status_code=404, detail="Receiver account not found.")

    # Raise the exception when the sender has insufficient funds
    if sender_account.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance.")

    # Create a new transaction record
    transaction = Transaction(from_account_id=sender_id, to_account_id=receiver_id, amount=amount,
                              transaction_type="transfer", status="pending")

    # Add the record to the database
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Update balances on both accounts
    sender_account.balance -= amount
    receiver_account.balance += amount
    db.commit()

    return {"message": "Transaction created", "transaction_id": transaction.id}
