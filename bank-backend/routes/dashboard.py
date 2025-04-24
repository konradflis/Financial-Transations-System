from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth import admin_required, user_required, hash_password
from src.database import get_db
from src.models import User, Account, Atm_device
from pydantic import BaseModel, constr
import random


router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(current_user=Depends(admin_required)):
    return {"message": "Welcome, admin!"}

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: int  # bo to 10-cyfrowe ID
    password: str ## alternatywnie: constr(min_length=6)  # może być więcej walidacji
    #role: str

@router.post("/admin/add-user")
def create_user_admin(user: UserCreate, db: Session = Depends(get_db)):
    # Sprawdź, czy email lub username (ID) już istnieje
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


@router.delete("/admin/delete-user", response_model=dict)
def delete_user(username: int, db: Session = Depends(get_db)):
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

@router.post("/admin/add-account", response_model=dict)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
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

@router.delete("/admin/delete-account", response_model=dict)
def delete_account(account_number: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == account_number).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(account)
    db.commit()
    return {"message": f"Account {account_number} successfully deleted"}


# Schemat danych wejściowych
class AtmDeviceCreate(BaseModel):
    localization: str #constr(min_length=1, max_length=20)
    status: str #constr(min_length=1, max_length=10)

@router.post("/admin/add-atm", response_model=dict)
def create_atm(atm: AtmDeviceCreate, db: Session = Depends(get_db)):
    try:
        new_atm = Atm_device(
            localization=atm.localization,
            status=atm.status
        )
        db.add(new_atm)
        db.commit()
        db.refresh(new_atm)
        return {"message": "ATM device created", "atm_id": new_atm.id}
    except Exception as e:
        print(f"Error: {e}")  # Logowanie błędu
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.delete("/admin/delete-atm", response_model=dict)
def delete_atm(atm_id: int, db: Session = Depends(get_db)):
    atm = db.query(Atm_device).filter(Atm_device.id == atm_id).first()

    if not atm:
        raise HTTPException(status_code=404, detail="ATM device not found")

    db.delete(atm)
    db.commit()
    return {"message": f"ATM device with ID {atm_id} deleted"}



@router.get("/user/dashboard")
def user_dashboard(current_user=Depends(user_required), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Witaj, {user.first_name}", "first_name": user.first_name}