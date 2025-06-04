import random
from src.database import get_db
from src.models import AtmDevice
from sqlalchemy.orm import Session

krakow_streets = [
    "ul. Floriańska", "ul. Grodzka", "ul. Szewska", "ul. Kanonicza", "ul. Basztowa",
    "ul. Westerplatte", "ul. Długa", "ul. Karmelicka", "ul. Starowiślna", "ul. Lubicz",
    "ul. Miodowa", "ul. Sławkowska", "ul. Pawia", "ul. Św. Tomasza", "ul. Dietla",
    "ul. Zwierzyniecka", "ul. Monte Cassino", "ul. Retoryka", "ul. Krowoderska",
    "ul. Bocheńska", "ul. Rakowicka", "ul. Meiselsa", "ul. Józefińska", "ul. Czapskich",
    "ul. Dunajewskiego", "ul. Szpitalna", "ul. Kopernika", "ul. Lea", "ul. Lubomirskiego",
    "ul. Olszańska", "ul. Długosza", "ul. Mikołajska", "ul. Starowiślna", "ul. Dietla",
    "ul. Kamienna", "ul. Zielińskiego", "ul. Łobzowska", "ul. Rakowicka", "ul. Królewska",
    "ul. Prądnicka", "ul. Bujaka", "ul. Armii Krajowej", "ul. Monte Cassino", "ul. Królewska",
    "ul. Wadowicka", "ul. Mogilska", "ul. Grota-Roweckiego", "ul. Łużycka", "ul. Koszykarska",
    "ul. Celna", "ul. Łobzowska", "ul. Mehoffera", "ul. Chmieleniec", "ul. Forteczna",
    "ul. Kalwaryjska", "ul. Bracka", "ul. Węgierska", "ul. Ludowa", "ul. Topolowa",
    "ul. Różana", "ul. Nadwiślańska", "ul. Cystersów", "ul. Wielicka", "ul. Zakopiańska",
    "ul. Powstańców Wielkopolskich", "ul. Lipska", "ul. Myśliwska", "ul. Wesoła",
    "ul. Mogilska", "ul. Żułowska", "ul. Konopnickiej", "ul. Kamieńskiego", "ul. Twardowskiego",
    "ul. Pędzichów", "ul. Witosa", "ul. Pilczycka", "ul. Księcia Józefa", "ul. Białoruska",
    "ul. Kluczborska", "ul. Bobrzyńskiego", "ul. Brożka", "ul. Banacha", "ul. Wybickiego",
    "ul. Reja", "ul. Na Zjeździe", "ul. Karmelicka", "ul. Krupnicza", "ul. Garncarska",
    "ul. Kopernika", "ul. Lubicz", "ul. Pijarska", "ul. Królowej Jadwigi", "ul. Szeroka",
    "ul. Łazarza", "ul. Na Kozłówce", "ul. Czarnowiejska", "ul. Sikorskiego", "ul. Wita Stwosza",
    "ul. Łokietka", "ul. Kazimierza Wielkiego", "ul. Senatorska", "ul. Olszańska",
]

def add_atm(db: Session, localization: str, status: str = "active"):
    new_atm = AtmDevice(localization=localization, status=status)
    db.add(new_atm)
    db.commit()
    db.refresh(new_atm)
    print(f"Dodano bankomat id={new_atm.id}, lokalizacja='{localization}', status='{status}'")

def main():
    db = next(get_db())
    try:
        for i in range(20):
            street = random.choice(krakow_streets)
            # Możemy dopisać numer domu losowo 1-100, żeby lokalizacje były unikalne:
            number = random.randint(1, 100)
            localization = f"{street} {number}"
            add_atm(db, localization)
    finally:
        db.close()

if __name__ == "__main__":
    main()
