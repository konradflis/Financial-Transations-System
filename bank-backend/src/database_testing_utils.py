import requests
import random
import string
from src.database import get_db
from src.models import User, Account
from pytz import timezone
from datetime import datetime, timedelta
import json
import os

## skrypt do dodawania wielu uzytkowników
## aby uruchomić, należy otworzyć projekt jako folder bank-backend --> konieczne, ze względu na ścieżki

url = "http://localhost:8000/bank_employee/add-user"

## funkcja do tworzenia kart przypisanych do użytkownika
def create_card_for_account(account_id):
    pin = ''.join(random.choices("123456789", k=4))  ########## error analogiczny jak z user: nie może być 0 wiodące
    card_data = {
        "account_id": account_id,
        "pin": pin
    }
    card_url = "http://localhost:8000/bank_employee/create-card"
    response = requests.post(card_url, json=card_data)
    return response

def login_as_employee():
    login_url = "http://localhost:8000/login"
    login_data = {
        "username": "1000000001",
        "password": "emp"
    }
    response = requests.post(login_url, data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.text}")

def get_dynamic_atm_id():
    try:
        r = requests.get("http://localhost:8000/atm-assignment")
        if r.status_code == 200:
            return r.json().get("atm_id")
        else:
            print("Błąd pobierania atm_id, status:", r.status_code)
            return None
    except Exception as e:
        print("Wyjątek przy pobieraniu atm_id:", e)
        return None



# Funkcja do generowania losowego hasła
def generate_random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Funkcja do generowania losowych danych użytkownika
def generate_random_user(db):
    first_name = ''.join(random.choices(string.ascii_uppercase, k=5))
    last_name = ''.join(random.choices(string.ascii_uppercase, k=5))
    email = f"{first_name.lower()}.{last_name.lower()}@example.com"
    # Generowanie unikalnego username (10-cyfrowego numeru)
    while True:
        username = random.randint(100000000, 999999999)  # 10-cyfrowy numer
        # Sprawdź, czy username już istnieje w bazie
        existing_user = db.query(User).filter(User.username == username).first()
        if not existing_user:  # Jeśli użytkownik o tym username nie istnieje, zakończ
            break

    password = generate_random_password()
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "username": username,
        "password": password,
        "role":"user"
    }

# Funkcja do dodawania wielu użytkowników
def add_multiple_users(db, num_users, token):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(num_users):
        user_data = generate_random_user(db)
        response = requests.post(url, json=user_data, headers=headers)

        if response.status_code == 200:
            print(f"User {user_data['username']} added successfully!")
        else:
            print(f"Error adding user {user_data['username']}: {response.text}")


# Funkcja do tworzenia konta dla użytkownika
def create_account_for_user(user_id, token, initial_balance=0.0):
    account_data = {
        "user_id": user_id,
        "initial_balance": initial_balance
    }
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.post("http://localhost:8000/bank_employee/add-account",
                             json=account_data, headers=headers)
    return response



# Funkcja do dodania wielu kont użytkownikom
def create_accounts_for_users(min_accounts: int, max_accounts: int, token: str):
    db = next(get_db())
    users = db.query(User).all()

    for user in users:
        num_accounts = random.randint(min_accounts, max_accounts)
        print(f"Creating {num_accounts} accounts for user {user.id} ({user.first_name} {user.last_name})")

        for _ in range(num_accounts):

            ## creating account
            balance = round(random.uniform(0, 10000), 2)  # przykładowe saldo
            response = create_account_for_user(user.id, token, balance)

            if response.status_code == 200:
                print(f" Account created for user {user.id}")

                account_id = response.json().get("account_id")  # zakładam, że endpoint zwraca id konta
                if account_id:
                    card_response = create_card_for_account(account_id)
                    if card_response.status_code == 200:
                        print(f"  Card created for account {account_id}")
                    else:
                        print(f"  Error creating card for account {account_id}: {card_response.text}")
            else:
                print(f" Error creating account for user {user.id}: {response.text}")


####################################### functions for testing module:
def get_all_accounts(db):
    account_data = db.query(Account.account_number, Account.balance).filter(Account.status == "active").all()
    return account_data


def generate_transaction_logs_auto_filename(db, count: int = 50, folder: str = "test_logs"):
    import random, json, os
    from datetime import datetime
    from pytz import timezone

    warsaw_tz = timezone("Europe/Warsaw")
    os.makedirs(folder, exist_ok=True)

    existing_files = [
        f for f in os.listdir(folder)
        if f.startswith(f"transactions_{count}_v") and f.endswith(".json")
    ]
    version = len(existing_files) + 1
    filename = f"transactions_{count}_v{version}.json"
    filepath = os.path.join(folder, filename)

    accounts = db.query(Account).filter(Account.status == "active").all()
    if not accounts:
        raise ValueError("Brak aktywnych kont w systemie.")

    account_balances = {acc.account_number: acc.balance for acc in accounts}
    transactions = []

    for _ in range(count):
        tx_type = random.choice(["transfer", "withdrawal", "deposit"])

        if tx_type == "transfer":
            valid_sources = [acc for acc in accounts if account_balances[acc.account_number] >= 5]
            if not valid_sources:
                continue
            from_account = random.choice(valid_sources)
            to_account = random.choice([
                acc for acc in accounts
                if acc.account_number != from_account.account_number
            ])

            max_amount = round(account_balances[from_account.account_number] * 0.8, 2)
            if max_amount < 1:
                continue
            amount = round(random.uniform(1, max_amount), 2)

            account_balances[from_account.account_number] -= amount
            account_balances[to_account.account_number] += amount

            transaction = {
                "type": "transfer",
                "sender_account": from_account.account_number,
                "receiver_account": to_account.account_number,
                "amount": amount,
                "username": str(from_account.user.username),
                "password": from_account.user.password,
            }

        elif tx_type == "withdrawal":
            valid_accounts = [acc for acc in accounts if account_balances[acc.account_number] >= 5 and acc.card]
            if not valid_accounts:
                continue
            account = random.choice(valid_accounts)

            max_amount = round(account_balances[account.account_number] * 0.8, 2)
            if max_amount < 1:
                continue
            amount = random.randint(1, 100) * 10  # losuje liczbę z przedziału 10, 20, ..., 1000

            selected_card = random.choice(account.card) #wybór losowej karty (przyp. do tego konta)

            account_balances[account.account_number] -= amount

            transaction = {
                "type": "withdrawal",
                "sender_account": account.account_number,
                "receiver_account": None,
                "amount": amount,
                "card_id": selected_card.id,
                "pin": str(selected_card.pin)
            }

        elif tx_type == "deposit":
            valid_accounts = [acc for acc in accounts if acc.card]
            if not valid_accounts:
                continue
            account = random.choice(valid_accounts)
            amount = random.randint(1, 100) * 10  # losuje liczbę z przedziału 10, 20, ..., 1000

            selected_card = random.choice(account.card)  # wybór losowej karty (przyp. do tego konta)

            account_balances[account.account_number] += amount

            transaction = {
                "type": "deposit",
                "sender_account": None,
                "receiver_account": account.account_number,
                "amount": amount,
                "card_id": selected_card.id,
                "pin": str(selected_card.pin)
            }

        transactions.append(transaction)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=4, ensure_ascii=False)

    print(f"Zapisano {len(transactions)} transakcji do pliku: {filepath}")
    return filepath

def main():
    db = next(get_db())  # Pobieramy sesję bazy danych

    #token = login_as_employee() ## login - bank emp
    #add_multiple_users(db, 2, token)  # Dodajemy 2 użytkowników
    #create_accounts_for_users(1,3, token)

    #generate_transaction_logs_auto_filename(db)

if __name__ == "__main__":
    main()