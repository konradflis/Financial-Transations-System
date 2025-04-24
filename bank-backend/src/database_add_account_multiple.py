import requests
import random
from src.database import get_db
from src.models import User

## skrypt do dodawania wielu kont
## aby uruchomić, należy otworzyć projekt jako folder bank-backend --> konieczne, ze względu na ścieżki

# Endpoint do dodawania kont
url = "http://localhost:8000/admin/add-account"

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


if __name__ == "__main__":
    create_accounts_for_users(min_accounts=1, max_accounts=5)
