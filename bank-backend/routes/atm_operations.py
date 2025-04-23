from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Transaction, Account, Card
from pydantic import BaseModel

router = APIRouter()


# Define the withdrawal model
class WtihdrawalModel(BaseModel):
    card_id: int
    atm_id: float
    amount: float


@router.post("/withdrawal")
def withdraw_funds(withdrawal_data: WtihdrawalModel, db: Session = Depends(get_db),
                   pin: str = Form(...)):

    card_id = withdrawal_data.card_id
    atm_id = withdrawal_data.atm_id
    amount = withdrawal_data.amount

    # TODO: Check if the ATM exists

    # Raise the exception when the card is not registered in the database (it does not exist)
    card_data = db.query(Card).filter(Card.id == card_id).first()
    if not card_data:
        raise HTTPException(status_code=404, detail="Please insert a valid card.")

    # Raise the exception when the PIN is incorrect
    pin_data = db.query(Card).filter(Card.id == card_id, Card.pin == pin).first()
    if not pin_data:
        raise HTTPException(status_code=401, detail="The PIN is incorrect.")

    # Raise the exception when the funds are insufficient
    account_data = card_data.account
    if account_data.balance < amount:
        raise HTTPException(status_code=409, detail="Insufficient funds.")

    # Raise the exception when the requested amount is impossible to be withdrawn
    if amount % 10 != 0:
        raise HTTPException(status_code=409, detail="The requested amount cannot be withdrawn.")
    # TODO: Check if the ATM can issue the requested amount

    # TODO: Create a withdrawal record, add it to the database

    # Update the balance
    # account_data.balance -= amount
    # db.commit()

    # TODO: Update the ATM table

    return {"message": "Withdrawal finished successfully!"}