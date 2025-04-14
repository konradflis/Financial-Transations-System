from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"client_encoding": "UTF8"})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Database session generator.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

