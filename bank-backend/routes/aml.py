import redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth import aml_required, hash_password
from src.database import get_db
from src.models import User, Account, AtmDevice
import random
from pydantic import BaseModel, constr
from typing import Optional, List

router = APIRouter()
r = redis.Redis(host='localhost', port=6379, db=0)

# TODO: Implement AML logic