from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth import admin_required, user_required
from src.database import get_db
from src.models import User
from pydantic import BaseModel


router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(current_user=Depends(admin_required)):
    return {"message": "Welcome, admin!"}

## dodawanie usera
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
        password=user.password,
        role="user"
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "User created", "user_id": db_user.id}



@router.get("/user/dashboard")
def user_dashboard(current_user=Depends(user_required), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Witaj, {user.first_name}", "first_name": user.first_name}