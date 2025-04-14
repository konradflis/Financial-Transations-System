import redis
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from src.auth import admin_required
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.models import User
from src.database import get_db
from src.auth import verify_password, create_access_token, store_token_in_redis
from datetime import timedelta

router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(current_user=Depends(admin_required)):
    return {"message": "Welcome, admin!"}