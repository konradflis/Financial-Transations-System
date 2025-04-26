import redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth import bank_employee_required, hash_password
from src.database import get_db
from src.models import User, Account, Atm_device
import random
from pydantic import BaseModel, constr
from typing import Optional, List

router = APIRouter()
r = redis.Redis(host='localhost', port=6379, db=0)


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: int  # bo to 10-cyfrowe ID
    password: str ## alternatywnie: constr(min_length=6)  # może być więcej walidacji
    #role: str

@router.post("/bank_employee/add-user")
def create_user_admin(user: UserCreate, db: Session = Depends(get_db), current_user=Depends(bank_employee_required)):
    existing_user = db.query(User).filter((User.email == user.email) | (User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Utwórz użytkownika
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        username=user.username,
        password=hash_password(user.password),
        role="user"
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "User created", "user_id": db_user.id}


@router.delete("/bank_employee/delete-user", response_model=dict)
def delete_user(username: int, db: Session = Depends(get_db), current_user=Depends(bank_employee_required)):
    # Sprawdź, czy użytkownik istnieje
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Usuń użytkownika z bazy
    db.delete(user)
    db.commit()
    return {"message": f"User {username} deleted"}

class AccountCreate(BaseModel):
    user_id: int
    initial_balance: float = 0.0

def generate_account_number():
    # Generowanie 26-cyfrowego numeru konta
    return ''.join([str(random.randint(0, 9)) for _ in range(26)])

@router.post("/bank_employee/add-account", response_model=dict)
def create_account(account: AccountCreate, db: Session = Depends(get_db), current_user=Depends(bank_employee_required)):
    # Sprawdzenie czy użytkownik istnieje
    user = db.query(User).filter(User.id == account.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generowanie unikalnego numeru konta
    while True:
        account_number = generate_account_number()
        existing_account = db.query(Account).filter(Account.account_number == account_number).first()
        if not existing_account:
            break  # numer jest unikalny

    # Tworzenie konta
    new_account = Account(
        user_id=account.user_id,
        account_number=account_number,
        balance=account.initial_balance,
        status="ok"
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)


    return {
        "message": "Account created",
        "account_id": new_account.id,
        "account_number": new_account.account_number,
        "length_account": len(account_number),
    }

@router.delete("/bank_employee/delete-account", response_model=dict)
def delete_account(account_number: str, db: Session = Depends(get_db), current_user=Depends(bank_employee_required)):
    account = db.query(Account).filter(Account.account_number == account_number).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(account)
    db.commit()
    return {"message": f"Account {account_number} successfully deleted"}


@router.get("/bank_employee/user-data", response_model=dict)
def get_user_data(
    username: int,
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username, User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    accounts = db.query(Account).filter(Account.user_id == user.id).all()

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        },
        "accounts": [
            {
                "id": acc.id,
                "account_number": acc.account_number,
                "balance": acc.balance,
                "status" : acc.status
            }
            for acc in accounts
        ]
    }


