from fastapi import FastAPI
from routes.transactions import router as transactions_router
from src.database import engine
from src.models import Base

app = FastAPI()

app.include_router(transactions_router)

Base.metadata.create_all(bind=engine)