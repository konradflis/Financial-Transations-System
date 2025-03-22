from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Transaction

router = APIRouter()

@router.post("/transfer")
def create_transfer(sender_id: int, receiver_id: int, amount: float, db: Session = Depends(get_db)):
    transaction = Transaction(
        from_account_id=sender_id,
        to_account_id=receiver_id,
        amount=amount,
        transaction_type="transfer",
        status="pending",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return {"message": "Transaction created", "transaction_id": transaction.id}