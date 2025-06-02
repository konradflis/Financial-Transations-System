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
def add_multiple_users(db, num_users):
    for _ in range(num_users):
        user_data = generate_random_user(db)
        response = requests.post(url, json=user_data)

        if response.status_code == 200:
            print(f"User {user_data['username']} added successfully!")
        else:
            print(f"Error adding user {user_data['username']}: {response.text}")


## skrypt do dodawania wielu kont
## aby uruchomić, należy otworzyć projekt jako folder bank-backend --> konieczne, ze względu na ścieżki

# Endpoint do dodawania kont
url = "http://localhost:8000/bank_employee/add-account"

# Funkcja do tworzenia konta dla użytkownika
def create_account_for_user(user_id, initial_balance=0.0):
    account_data = {
        "user_id": user_id,
        "initial_balance": initial_balance
    }
    response = requests.post(url, json=account_data)
    return response

# Funkcja do dodania wielu kont użytkownikom
def create_accounts_for_users(min_accounts: int, max_accounts: int):
    db = next(get_db())
    users = db.query(User).all()

    for user in users:
        num_accounts = random.randint(min_accounts, max_accounts)
        print(f"Creating {num_accounts} accounts for user {user.id} ({user.first_name} {user.last_name})")

        for _ in range(num_accounts):
            balance = round(random.uniform(0, 10000), 2)  # przykładowe saldo
            response = create_account_for_user(user.id, balance)

            if response.status_code == 200:
                print(f" Account created for user {user.id}")
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
                "from_account_number": from_account.account_number,
                "to_account_number": to_account.account_number,
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
            amount = round(random.uniform(1, max_amount), 2)

            account_balances[account.account_number] -= amount

            transaction = {
                "type": "withdrawal",
                "from_account_number": account.account_number,
                "to_account_number": None,
                "amount": amount,
                "pin": random.choice(account.card).pin if account.card else None ##random w związku z tym, że może być więcej niż jedna karta do konta
            }

        elif tx_type == "deposit":
            valid_accounts = [acc for acc in accounts if acc.card]
            if not valid_accounts:
                continue
            account = random.choice(valid_accounts)
            amount = round(random.uniform(10, 1000), 2)

            account_balances[account.account_number] += amount

            transaction = {
                "type": "deposit",
                "from_account_number": None,
                "to_account_number": account.account_number,
                "amount": amount,
                "pin": random.choice(account.card).pin if account.card else None ##random w związku z tym, że może być więcej niż jedna karta do konta
            }

        transactions.append(transaction)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=4, ensure_ascii=False)

    print(f"Zapisano {len(transactions)} transakcji do pliku: {filepath}")
    return filepath

def main():
    db = next(get_db())  # Pobieramy sesję bazy danych
    #add_multiple_users(db, 2)  # Dodajemy 2 użytkowników
    generate_transaction_logs_auto_filename(db)

if __name__ == "__main__":
    main()