from fastapi import APIRouter, Depends
from src.auth import admin_required, user_required


router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(current_user=Depends(admin_required)):
    return {"message": "Welcome, admin!"}


@router.get("/user/dashboard")
def user_dashboard(current_user=Depends(user_required)):
    return {"message": "Welcome, user!"}