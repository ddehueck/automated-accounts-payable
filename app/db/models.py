from secrets import token_urlsafe

import ulid
from sqlalchemy import (ARRAY, DECIMAL, Boolean, Column, DateTime, Float,
                        ForeignKey, Integer, String, UniqueConstraint, alias)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


def generate_token():
    return token_urlsafe(128)


class User(Base):
    __tablename__ = "users"

    id = Column(String, default=ulid.ulid, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"))
    invoices = relationship("Invoice")

    name = Column(String, nullable=True)
    paid_plan = Column(String, nullable=True)
    stripe_session_id = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class ResetPasswordToken(Base):
    __tablename__ = "reset_password_tokens"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, default=generate_token, nullable=False)
    created_on = Column(DateTime, server_default=func.now())


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, default=ulid.ulid, primary_key=True)
    users = relationship("User")
    invoices = relationship("Invoice")

    name = Column(String)
    address = Column(String)
    legal_business_type = Column(String)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    invoices = relationship("Invoice")

    name = Column(String)
    aliases = Column(ARRAY(String), default=[])
    contact_email = Column(String)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True, index=True)
    content_hash = Column(String)

    is_paid = Column(Boolean, default=False)
    vendor_name = Column(String)
    amount_due = Column(DECIMAL)
    currency = Column(String)
    due_date = Column(DateTime)
    invoice_id = Column(String)
    image_uri = Column(String)

    raw_vendor_name = Column(String)
    raw_amount_due = Column(String)
    raw_due_date = Column(String)

    category_links = relationship("CategoryInvoiceAssociation", back_populates="invoice")

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)

    name = Column(String, unique=True)

    invoice_links = relationship("CategoryInvoiceAssociation", back_populates="category")

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class CategoryInvoiceAssociation(Base):
    __tablename__ = "category_invoice_associations"

    category_id = Column(ForeignKey("categories.id"), primary_key=True)
    invoice_id = Column(ForeignKey("invoices.id"), primary_key=True)

    category = relationship("Category", back_populates="invoice_links")
    invoice = relationship("Invoice", back_populates="category_links")
