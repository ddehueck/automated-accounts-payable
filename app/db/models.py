from locale import currency
from secrets import token_urlsafe

import ulid
from sqlalchemy import (DECIMAL, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, default=ulid.ulid, primary_key=True)

    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    paid_plan = Column(String, nullable=True)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


def generate_token():
    return token_urlsafe(128)


class ResetPasswordToken(Base):
    __tablename__ = "reset_password_tokens"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, default=generate_token, nullable=False)
    created_on = Column(DateTime, server_default=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    vendor_name = Column(String)
    amount_due = Column(DECIMAL)
    currency = Column(String)
    due_date = Column(DateTime)
    invoice_id = Column(String)

    raw_vendor_name = Column(String)
    raw_amount_due = Column(String)
    raw_due_date = Column(String)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())
