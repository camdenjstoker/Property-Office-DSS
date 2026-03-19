"""
SQLAlchemy ORM Models for Property-Office-DSS
Maps to the database schema defined in Database/Property Office Script.sql
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Instrument(Base):
    """
    Instrument table model.
    Represents musical instruments in the collection with tracking for rentals, returns, and condition.
    """
    __tablename__ = "instrument"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_type = Column(String(255))
    instrument_section = Column(String(255))
    instrument_barcode = Column(String(255), unique=True, nullable=True)
    instrument_call_number = Column(String(255), nullable=True)
    instrument_serial_number = Column(String(255), nullable=True)
    instrument_asset_tag = Column(String(255), nullable=True)
    instrument_make = Column(String(255), nullable=True)
    instrument_model = Column(String(255), nullable=True)
    instrument_location = Column(String(255), nullable=True)
    instrument_condition = Column(String(50), nullable=True)  # e.g., "good", "fair", "poor"
    instrument_last_rented = Column(DateTime, nullable=True)
    instrument_last_returned = Column(DateTime, nullable=True)
    last_inventory = Column(DateTime, nullable=True)
    last_cleaned = Column(DateTime, nullable=True)
    instrument_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Instrument(id={self.id}, type={self.instrument_type}, "
            f"barcode={self.instrument_barcode})>"
        )


class Book(Base):
    """Book/Library holdings model."""
    __tablename__ = "books"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_type = Column(String(255))
    barcode = Column(String(255), unique=True, nullable=True)
    location = Column(String(255), nullable=True)
    bookscol = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=True)
    condition = Column(String(50), nullable=True)
    book_name = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    last_inventoried = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Book(id={self.id}, name={self.book_name})>"


class Accessory(Base):
    """Accessory/Equipment model."""
    __tablename__ = "accessory"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    accessory_type = Column(String(255))
    barcode = Column(String(255), unique=True, nullable=True)
    location = Column(String(255), nullable=True)
    brand = Column(String(255), nullable=True)
    condition = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Accessory(id={self.id}, type={self.accessory_type})>"


class Locker(Base):
    """Storage locker model."""
    __tablename__ = "locker"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    locker_type = Column(String(255))
    locker_priority = Column(String(50), nullable=True)
    locker_room = Column(String(255), nullable=True)
    locks = Column(String(255), nullable=True)
    locker_code = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Locker(id={self.id}, room={self.locker_room})>"


class User(Base):
    """User/Staff model."""
    __tablename__ = "user"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    f_name = Column(String(255))
    l_name = Column(String(255))
    I_num = Column(String(255), unique=True, nullable=True)
    Role = Column(String(100), nullable=True)
    usercol = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, name={self.f_name} {self.l_name})>"


class KeyLock(Base):
    """Key/Lock combination tracking model."""
    __tablename__ = "keys_locks"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    locks_new_number = Column(String(255), nullable=True)
    locks_old_number = Column(String(255), nullable=True)
    combination = Column(String(255), nullable=True)
    barcode = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<KeyLock(id={self.id}, lock={self.locks_new_number})>"


class Financial(Base):
    """Financial/Transaction record model."""
    __tablename__ = "financial"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    financial_date = Column(DateTime, default=datetime.utcnow)
    financial_amount = Column(Float, nullable=True)
    financial_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Financial(id={self.id}, amount={self.financial_amount})>"


class WebhookAuditLog(Base):
    """
    Audit log for all webhook transactions.
    Provides visibility into every check-in/check-out event from Cheqroom.
    """
    __tablename__ = "webhook_audit_log"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, nullable=False)
    event_type = Column(String(50))  # "checked_in" or "checked_out"
    user_name = Column(String(500), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    timestamp_from_cheqroom = Column(DateTime)
    timestamp_processed = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50))  # "success", "ignored", "error"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<WebhookAuditLog(id={self.id}, instrument={self.instrument_id}, "
            f"event={self.event_type})>"
        )
