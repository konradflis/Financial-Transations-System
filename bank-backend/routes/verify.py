from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Transaction, Account, Card, AtmDevice, User
from pydantic import BaseModel
from datetime import datetime


# Weryfikacja transakcji ATM
router = APIRouter()

# Model do automatycznej weryfikacji
class TransactionVerificationModel(BaseModel):
    transaction_id: int
    from_account_id: int
    to_account_id: int
    amount: float
    type: str
    status: str
    date: datetime
    device_id: int


@router.post("/verify-transaction-auto")
def auto_verify(transaction_data: TransactionVerificationModel, db: Session = Depends(get_db)):

    # Sprawdzenie, czy transakcja jest w bazie
    transaction_data_actual = db.query(Transaction).filter(Transacation.id == transaction_data.transaction_id).first()
    if not transaction_data_actual:
        raise HTTPException(status_code=404, detail="Nie znaleziono transakcji.")

    # Sprawdzenie, czy rekordy są zgodne
    expected = TransactionVerificationModel.model_validate(transaction_data_actual)
    if expected.model_dump() != transaction_data.model_dump():
        raise HTTPException(status_code=404, detail="Nie znaleziono transakcji.")

    # Sprawdzenie, czy status jest oczekujący
    if transaction_data.status != 'pending':
        raise HTTPException(status_code=403, detail="Transakcja nie jest oczekująca.")

    # Dla kwot niższych od wybranego progu — automatyczna akceptacja
    if transaction_data.amount <= 20000:

        return {"message": "Weryfikacja zakończona pomyślnie.", "status": "completed"}

    # Dla kwot wyższych — przekierowanie do pracownika (weryfikacja ręczna)
    # TODO: Poczekaj na response innego endpointa
    else:
        return {"message": "Wymagana szczegółowa weryfikacja.", "status": "pending"}