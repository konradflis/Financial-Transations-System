from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth import admin_required, user_required
from src.database import get_db
from src.models import User


router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(current_user=Depends(admin_required)):
    return {"message": "Welcome, admin!"}


@router.get("/user/dashboard")
def user_dashboard(current_user=Depends(user_required), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Witaj, {user.first_name}", "first_name": user.first_name}