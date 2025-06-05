from celery import Celery
from models import AtmDevice, Card, Account, User, Transaction
from database import get_db
import requests
from datetime import datetime
import pytz
import sys

from routes.aml import send_transaction_to_aml


celery_app = Celery("worker", broker="redis://redis:6379/0")

@celery_app.task(name="create_transaction")
def create_transaction(user_id: int, sender_account: str, receiver_account: str, amount: float):

    db = next(get_db())

    try:
        sender_account = db.query(Account).filter(Account.account_number == sender_account,
                                                  Account.user_id == user_id).first()
        sender_id = sender_account.id

        if not sender_account:
            raise Exception(f"Account not found: {sender_account}")

        # Check if receiver is in our database (if not, it is an external transfer)
        receiver_account = db.query(Account).filter(Account.account_number == receiver_account).first()
        if receiver_account:
            receiver_id = receiver_account.id
        else:
            receiver_id = 0  # default account for external transfers

        if sender_account.balance < amount:
            return {"status": "failure", "message": "insufficient balance"}

        # Create a new transaction record
        transaction = Transaction(from_account_id=sender_id, to_account_id=receiver_id, amount=amount,
                                  type="transfer", status="pending")

        # Add the record to the database
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        celery_app.send_task("process_aml_check", args=[transaction.id, amount])  # Przeniesienie taska do workera

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@celery_app.task(name="process_aml_check")
def process_aml_check(transaction_id: int, amount: float):

    db = next(get_db())
    try:
        send_transaction_to_aml(transaction_id, amount)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@celery_app.task(name="process_atm_operation_task")         # wywołuje się
def process_atm_operation_task(transaction_id: int):        # kolejkowanie operacji bankomatowych ig

    db = next(get_db())

    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            return

        # rozgraniczenie na dwie rodzaje transakcji - wplaty/wyplaty --> roznica w tym czy to from_account, czy to_account
        if transaction.type == "withdrawal":
            account = db.query(Account).filter(Account.id == transaction.from_account_id).first()
        elif transaction.type == "deposit":
            account = db.query(Account).filter(Account.id == transaction.to_account_id).first()

        # Weryfikacja AML
        verification_response = requests.post(
            "http://bank-backend:8000/verify-transaction-auto",
            json={"transaction_id": transaction_id}
        )

        now = datetime.now(pytz.timezone('Europe/Warsaw'))


        if verification_response.status_code != 200:
            transaction.status = "failed"
            transaction.date = now
            db.commit()
            return

        result_status = verification_response.json().get("status")
        transaction.date = now

        if result_status == "completed":
            transaction.status = "completed"

            #rozgraniczenie czy balance na "+" czy "-"
            if transaction.type == "withdrawal":
                account.balance -= transaction.amount
                account.status = "active"
            elif transaction.type == "deposit":
                account.balance += transaction.amount
                account.status = "active"


        else:
            transaction.status = "pending"  # albo aml_blocked
            return


        db.commit()
        db.refresh(transaction)
    except Exception as e:
        db.rollback()
        print(f"Błąd przetwarzania transakcji ATM: {e}")
    finally:
        db.close()