import requests
import random
import string
from src.database import get_db
from src.models import User

## skrypt do dodawania wielu uzytkowników
## aby uruchomić, należy otworzyć projekt jako folder bank-backend --> konieczne, ze względu na ścieżki

url = "http://localhost:8000/admin/add-user"

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

def main():
    db = next(get_db())  # Pobieramy sesję bazy danych
    add_multiple_users(db, 2)  # Dodajemy 2 użytkowników

if __name__ == "__main__":
    main()