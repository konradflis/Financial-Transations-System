import redis
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.models import User
from src.database import get_db
from src.auth import verify_password, create_access_token, store_token_in_redis
from datetime import timedelta

r = redis.Redis(host='localhost', port=6379, db=0)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 30

@router.post("/login")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    username = form_data.username
    password = form_data.password
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username, "user_id": user.id},
                                       expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    store_token_in_redis(user.id, access_token, ACCESS_TOKEN_EXPIRE_MINUTES)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(user_id: int):
    token_key = f"user:{user_id}:token"

    if r.exists(token_key):
        r.delete(token_key)
        return {"message": "User logged out successfully"}
    else:
        raise HTTPException(status_code=404, detail="Token not found, user may not be logged in")

