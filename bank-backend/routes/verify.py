from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Transaction, Account, Card, AtmDevice, User
from pydantic import BaseModel
from datetime import datetime

from routes.aml import is_multiple_transactions_different_locations, is_smurfing_activity


# Weryfikacja transakcji ATM
router = APIRouter()

class AutoVerificationModel(BaseModel):
    transaction_id: int

@router.post("/verify-transaction-auto")
def auto_verify(transaction_pending: AutoVerificationModel, db: Session = Depends(get_db)):

    # Sprawdzenie, czy transakcja jest w bazie
    transaction_id = transaction_pending.transaction_id
    transaction_data = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction_data:
        raise HTTPException(status_code=404, detail="Nie znaleziono transakcji.")

    # Sprawdzenie, czy status jest oczekujący
    if transaction_data.status != 'pending':
        raise HTTPException(status_code=403, detail="Transakcja nie jest oczekująca.")

    # Dla kwot niższych od wybranego progu — automatyczna akceptacja
    if (transaction_data.amount <= 20000
            and not is_multiple_transactions_different_locations(db, transaction_data.from_account_id, transaction_data.type))\
            and not is_smurfing_activity(db,transaction_data.from_account_id,transaction_data.type):
        return {"message": "Weryfikacja zakończona pomyślnie.", "status": "completed"}

    # Dla kwot wyższych — przekierowanie do pracownika (weryfikacja ręczna)
    else:
        return {"message": "Wymagana szczegółowa weryfikacja.", "status": "pending"}


