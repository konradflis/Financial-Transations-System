from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Transaction, Account
from src.auth import get_current_user
from pydantic import BaseModel

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
    :return: information about successful transer
    """

    sender_account = transfer_data.sender_account
    receiver_account = transfer_data.receiver_account
    amount = transfer_data.amount

    # Raise the exception when sender account is not the user's account
    sender_account = db.query(Account).filter(Account.account_number == sender_account, Account.user_id == user_id).first()
    sender_id = sender_account.id

    if not sender_account:
        raise HTTPException(status_code=403, detail="You can only send money from your own account.")

    # Check if receiver is in our database (if not, it is an external transfer)
    receiver_account = db.query(Account).filter(Account.account_number == receiver_account).first()
    if receiver_account:
        receiver_id = receiver_account.id
    else:
        receiver_id = 0 # default account for external transfers

    # Raise the exception when the sender has insufficient funds
    if sender_account.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance.")


    # Create a new transaction record
    transaction = Transaction(from_account_id=sender_id, to_account_id=receiver_id, amount=amount,
                              type="transfer", status="pending")

    # Add the record to the database
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Update balances on both accounts
    sender_account.balance -= amount
    if receiver_account:
        receiver_account.balance += amount
    db.commit()

    return {"message": "Transaction created", "transaction_id": transaction.id}
