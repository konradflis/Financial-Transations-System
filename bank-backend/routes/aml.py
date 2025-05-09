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
        if amount > 10000:
            transaction.status = "aml_blocked"
            print(f"Transaction {transaction_id} is suspicious!")
        else:
            transaction.status = "aml_approved"
            print(f"Transaction {transaction_id} is normal.")





    else:
        raise HTTPException(status_code=405, detail="Transaction error: wrong transaction type")

    time.sleep(10)
    db.commit()

    return {"status": "checked", "new_status": transaction.status}