import uvicorn
import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.transactions import router as transactions_router
from routes.login import router as login_router
from routes.dashboard import router as dashboard_router
from routes.user import router as user_router
from routes.atm_operations import router as withdrawal_router
from routes.admin import router as admin_router
from routes.bank_employee import router as bank_employee_router
from routes.aml import router as aml_router
from src.database import engine
from src.models import Base

# Connect to the local redis server
r = redis.Redis(host='redis', port=6379, db=0)

# Create an instance of a FastAPI app, add selected routes
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions_router)
app.include_router(login_router)
app.include_router(withdrawal_router)
app.include_router(dashboard_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(bank_employee_router)
app.include_router(aml_router)


# Create the defined tables
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)   # Run the app
