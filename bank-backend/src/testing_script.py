import requests
import json
from fastapi import Depends

from src.database import get_db
from datetime import datetime

from database_testing_utils import get_dynamic_atm_id

from testing_clearing_atm import activate_busy_accounts, activate_busy_atms


input_data_path="test_logs/transactions_20_v2.json"
BASE_URL = "http://localhost:8000"  #backend

Session = Depends(get_db)

def process_transaction(txn):
    txn_type = txn["type"]

    try:
        if txn_type == "transfer":
            ## request - logowanie uzytkownika
            response_logging = requests.post(
                f"{BASE_URL}/login",
                data={
                    "username": txn["username"],
                    "password": txn["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response_logging.status_code == 200:
                print(f"{txn_type.title()} zakończony sukcesem:", response_logging.json())
                access_token = response_logging.json()["access_token"]
            else:
                print(f"Błąd podczas {txn_type}: {response_logging.status_code} {response_logging.text}")


            ## request - transfer
            response_transfer = requests.post(
                f"{BASE_URL}/transfer",
                json={
                    "sender_account": txn["sender_account"],
                    "receiver_account": txn["receiver_account"],
                    "amount": txn["amount"]
                },
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )

            ## request - wylogowanie uzytkownika
            response_logout = requests.post(
                f"{BASE_URL}/logout",
                params={"user_id": txn["user_id"]}  # Uwaga: to jest param w URL, nie body!
            )

            if response_logout.status_code == 200:
                print("Wylogowano użytkownika pomyślnie:", response_logout.json())
            else:
                print(f"Błąd podczas wylogowania: {response_logout.status_code} {response_logout.text}")



        elif txn_type == "deposit":
            response_pin_verification = requests.post(
                f"{BASE_URL}/atm-operation/pin-verification",
                json={
                    "card_id": txn["card_id"],
                    "pin": txn["pin"]
                }
            )

            if response_pin_verification.status_code == 200:
                print(f"{response_pin_verification} zakończony sukcesem:", response_pin_verification.json())
                #access_token = response_pin_verification.json()["access_token"]
            else:
                print(f"Błąd podczas response_pin_verification: {response_pin_verification.status_code} {response_pin_verification.text}")


            ## przyporzadkowanie wolnego atm:
            atm_id=get_dynamic_atm_id()

            response_deposit=requests.post(
                f"{BASE_URL}/atm-operation/deposit",
                json={
                    "card_id": txn["card_id"],
                    "pin": txn["pin"],
                    "amount": txn["amount"],
                    "atm_id": atm_id
                }
            )

            if response_deposit.status_code == 200:
                print(f"{response_deposit} zakończony sukcesem:", response_deposit.json())
                #access_token = response_pin_verification.json()["access_token"]
            else:
                print(f"Błąd podczas response_deposit: {response_deposit.status_code} {response_deposit.text}")



        elif txn_type == "withdrawal":
            response_pin_verification = requests.post(
                f"{BASE_URL}/atm-operation/pin-verification",
                json={
                    "card_id": txn["card_id"],
                    "pin": txn["pin"]
                }
            )

            if response_pin_verification.status_code == 200:
                print(f"{response_pin_verification} zakończony sukcesem:", response_pin_verification.json())
                # access_token = response_pin_verification.json()["access_token"]
            else:
                print(
                    f"Błąd podczas response_pin_verification: {response_pin_verification.status_code} {response_pin_verification.text}")

            ## przyporzadkowanie wolnego atm:
            atm_id = get_dynamic_atm_id()
            response_withdrawal = requests.post(
                f"{BASE_URL}/atm-operation/withdrawal",
                json={
                    "card_id": txn["card_id"],
                    "pin": txn["pin"],
                    "amount": txn["amount"],
                    "atm_id": atm_id
                }
            )

            if response_withdrawal.status_code == 200:
                print(f"{response_withdrawal} zakończony sukcesem:", response_withdrawal.json())
                # access_token = response_pin_verification.json()["access_token"]
            else:
                print(f"Błąd podczas response_withdrawal: {response_withdrawal.status_code} {response_withdrawal.text}")

        else:
            print(f"Nieznany typ transakcji: {txn_type}")
            return



    except Exception as e:
        print(f"Błąd podczas przetwarzania {txn_type}: {e}")


def main():
    start_time = datetime.now()
    print(f"Start przetwarzania: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    with open(input_data_path, "r", encoding="utf-8") as f:
        transactions = json.load(f)

    counter=0
    for txn in transactions:
        print(f"================== process: {counter} ================== ")
        process_transaction(txn)
        #print(txn)
        counter+=1
        print("")

    end_time = datetime.now()
    print(f"Koniec przetwarzania: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    duration = end_time - start_time
    print(f"Czas trwania: {duration} (czyli {duration.total_seconds():.2f} sekund)")

if __name__ == "__main__":
    main()
