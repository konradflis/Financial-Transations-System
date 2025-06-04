from src.database import get_db
from src.models import AtmDevice
from sqlalchemy.orm import Session
import random

def activate_busy_atms(db: Session):
    # Pobierz wszystkie bankomaty o statusie 'busy'
    busy_atms = db.query(AtmDevice).filter(AtmDevice.status == "busy").all()

    if not busy_atms:
        print("Brak bankomatów o statusie 'busy'.")
        return

    for atm in busy_atms:
        print(f"Zmiana statusu bankomatu id={atm.id} z 'busy' na 'active'")
        atm.status = "active"

    db.commit()
    print(f"Zmieniono status {len(busy_atms)} bankomatów na 'active'.")

def main():
    db = next(get_db())  # Pobranie sesji bazy danych
    try:
        activate_busy_atms(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
