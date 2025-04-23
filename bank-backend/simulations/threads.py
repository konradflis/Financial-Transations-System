import requests
import threading

users = [
    {"username": "1234567890", "password": "jkow"},
    {"username": "987654321", "password": "mkow"}
]

BASE_URL = "http://127.0.0.1:8000"

tokens = {}


def login_and_transfer(user):
    response = requests.post(f"{BASE_URL}/login", data=user)
    print(user, response)
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(user['username'], token, headers)
        transfer_data = {"sender_id": 1, "receiver_id": 4, "amount": 10}
        response = requests.post(f"{BASE_URL}/transfer", json=transfer_data, headers=headers)
        print(f"User {user['username']} transfer response: {response.json()}")


threads = []
for user in users:
    thread = threading.Thread(target=login_and_transfer, args=(user,))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

