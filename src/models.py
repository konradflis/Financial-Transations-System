from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()   # Base class


class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True, index=True)  # PK: Account ID
    account_number = Column(String(26), unique=True, index=True)  # Account number
    user_id = Column(Integer, ForeignKey('users.id'))  # FK: User
    balance = Column(Float, default=0.0)  # Account balance

    user = relationship("User", back_populates="accounts")
    card = relationship("Card", back_populates="cards")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)  # PK: User ID
    first_name = Column(String(100))  # First name
    last_name = Column(String(100))  # Last name
    email = Column(String(100), unique=True)  # Email
    username = Column(Integer, unique=True)  # 10 digit ID to log in
    password = Column(String(100))  # Password (TO DO: Encrypting)

    accounts = relationship("Account", back_populates="user")


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)  # PK: Transaction ID
    from_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)  # FK: Source account ID
    to_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)  # FK: Destination account ID
    amount = Column(Float, nullable=False)  # Amount
    transaction_type = Column(Enum("deposit", "withdrawal", "transfer", name="transaction_types"))  # Transaction type
    date = Column(DateTime, default=datetime.now(timezone.utc))  # Transaction date
    status = Column(Enum("pending", "completed", "failed", name="transaction_statuses"), default="pending")  # Transaction state

    from_account = relationship("Account", foreign_keys=[from_account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])

    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, date={self.date}, type={self.transaction_type})>"


class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    pin = Column(String(4), nullable=False)
    # TODO: potentially more columns

    account = relationship("Account", back_populates="cards")


# TODO: Create tables regarding withdrawals and deposits

# TODO: Create table regarding ATMs
