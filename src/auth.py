import jwt
import redis
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from src.config import ALGORITHM, SECRET_KEY

r = redis.Redis(host='localhost', port=6379, db=0)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    print(data)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def store_token_in_redis(user_id: int, token: str, expires_delta: timedelta):
    r.setex(f"user:{user_id}:token", expires_delta * 60, token)

def verify_token_in_redis(token: str, user_id: int):
    stored_token = r.get(f"user:{user_id}:token")
    if stored_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    if stored_token.decode() != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return True

def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        token_key = f"user:{user_id}:token"

        if not r.exists(token_key):
            raise HTTPException(status_code=401, detail="Invalid token or user logged out")

        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_all_tokens():
    keys = r.keys("user:*:token")
    tokens = {key.decode(): r.get(key).decode() for key in keys}
    return tokens
