from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, Account, Transaction, Card
from src.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


@router.get("/user/accounts")
def get_user_accounts(current_user: int = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(Account).filter_by(user_id=current_user).all()
    return [{"id": acc.id, "name": acc.account_number} for acc in accounts]


@router.get("/user/account/{account_id}/balance")
def get_account_balance(account_id: int, current_user: int = Depends(get_current_user), db: Session = Depends(get_db)):
    print(account_id)
    account = db.query(Account).filter_by(id=account_id, user_id=current_user).first()
    print(account)
    if not account:
        raise HTTPException(status_code=404, detail="Nie znaleziono konta")
    return {"balance": account.balance}


@router.get("/user/account/{account_id}/transactions")
def get_account_transactions(account_id: int, current_user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    account = db.query(Account).filter_by(id=account_id, user_id=current_user).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    transactions = db.query(Transaction).filter(
        (Transaction.from_account_id == account.id) | (Transaction.to_account_id == account.id)
    ).all()

    return [{"id": txn.id, "date": txn.date, "amount": txn.amount,
             "receiver": db.query(Account).filter_by(id=txn.to_account_id).first().account_number,
             "transaction_type": txn.type, "status": txn.status} for txn in
            transactions]


@router.get("/user/account/{account_id}/card_id")
def get_card_id(account_id: int, db: Session = Depends(get_db)):

    # Uzyskiwanie danych karty
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Niepoprawne dane konta.")

    #card = Card(account_id=account.id, pin="1234")
    #db.add(card)
    #db.commit()
    #db.refresh(card)

    card = db.query(Card).filter_by(account_id=account.id).first()
    print(card.id)
    if not card:
        raise HTTPException(status_code=404, detail="Brak dostępnych kart.")

    return {"card_id": card.id}


