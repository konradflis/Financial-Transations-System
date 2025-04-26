import jwt
import redis
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from src.config import ALGORITHM, SECRET_KEY

r = redis.Redis(host='redis', port=6379, db=0)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash the password.
    :param password: password
    :return: hashed password
    """

    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    """
    Verify the password.
    :param plain_password: original user password
    :param hashed_password: hashed password
    :return:
    """

    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta):
    """
    Create acces token.
    :param data: data
    :param expires_delta: token lifetime
    :return: token
    """

    # Copy the data
    to_encode = data.copy()
    print(data)

    # Set the expiration time
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def store_token_in_redis(user_id: int, token: str, expires_delta: timedelta):
    """
    Store the token in redis until it expires.
    :param user_id: user id
    :param token: token
    :param expires_delta: token lifetime
    """

    r.setex(f"user:{user_id}:token", int(expires_delta.total_seconds()), token)


def verify_token_in_redis(token: str, user_id: int):
    """
    Verify the stored token.
    :param token: token
    :param user_id: user id
    :return: true -- only when then the token was verified successfully
    """

    # Get the token associated with the user
    stored_token = r.get(f"user:{user_id}:token")

    # Raise appropriate exceptions when the token is None or invalid
    if stored_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if stored_token.decode() != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return True


def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    """
    Get the current user id.
    :param token: bearer token
    :return: user id
    """

    try:
        # Decode the token -- obtain the user data
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")

        token_key = f"user:{user_id}:token"

        # Raise the exception when token does not exist in redis
        if not r.exists(token_key):
            raise HTTPException(status_code=401, detail="Invalid token or user logged out")

        return user_id

    # Raise the exception when the token is invalid
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_all_tokens() -> dict:
    """
    Get all tokens.
    :return: dictionary with tokens
    """

    # Get keys matching the specifc pattern
    keys = r.keys("user:*:token")

    # Associate tokens with the keys
    tokens = {key.decode(): r.get(key).decode() for key in keys}

    return tokens


def admin_required(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return payload


def user_required(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("role") not in ["user", "admin"]:
        raise HTTPException(status_code=403, detail="Users only")
    return payload


def bank_employee_required(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("role") not in ["user", "bank_emp"]:
        raise HTTPException(status_code=403, detail="Bank employees only")
    return payload


def aml_required(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("role") not in ["user", "aml"]:
        raise HTTPException(status_code=403, detail="AML only")
    return payload



