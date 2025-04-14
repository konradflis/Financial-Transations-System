import uvicorn
import redis
from fastapi import FastAPI
from routes.transactions import router as transactions_router
from routes.login import router as login_router
from routes.atm_operations import router as withdrawal_router
from src.database import engine
from src.models import Base

# Connect to the local redis server
r = redis.Redis(host='localhost', port=6379, db=0)

# Create an instance of a FastAPI app, add selected routes
app = FastAPI()
app.include_router(transactions_router)
app.include_router(login_router)
app.include_router(withdrawal_router)

# Create the defined tables
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)   # Run the app
