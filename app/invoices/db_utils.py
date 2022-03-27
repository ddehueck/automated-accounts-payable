import re
from datetime import datetime
from typing import List, Optional
from unicodedata import name

import sqlalchemy as sa
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from app.db.models import Category, CategoryInvoiceAssociation, Invoice

from .models import CreateInvoice


def get_invoice_by_id(db: Session, invoice_id: str) -> Optional[Invoice]:
    return db.query(Invoice).filter_by(id=invoice_id).first()


def save_invoice(db: Session, invoice: CreateInvoice) -> Invoice:
    db_model = invoice.to_orm()
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def get_invoices_by_user(
    db: Session,
    user_id: str,
    filter_by: str = None,
    order_by: str = "due_date",
    limit: int = 100,
    offset: int = 0,
    desc: bool = False,
) -> List[Invoice]:
    """Retrieves invoices from db

    Args:
        db (Session): SessionLocal object
        user_id (str): User to pull invoices from
        order_by (str, optional): Name of column to order by. Defaults to "due_date".
        desc (bool, optional): Indicates if results should be sorted in a desc fashion or not (i.e. asc). Defaults to False.
        limit (int, optional): Max number of results to be returned. Defaults to 100.
        offset (int, optional): Offset to allow for pagination. Defaults to 0.

    Returns:
        List[Invoice]
    """
    order_by_stmt = getattr(Invoice, order_by)
    if desc:
        order_by_stmt = sa.desc(order_by_stmt)

    invoices_query = db.query(Invoice).filter_by(user_id=user_id).order_by(order_by_stmt)
    if filter_by == "paid":
        invoices_query = invoices_query.filter_by(is_paid=True)
    elif filter_by == "due":
        invoices_query = invoices_query.filter_by(is_paid=False)
    elif filter_by == "all":
        # TODO Add enumerations
        pass

    invoices_query = invoices_query.limit(limit).offset(offset)
    return invoices_query.all()


def update_paid_status_invoice(db: Session, invoice_id: str, is_paid: bool) -> Invoice:
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise ValueError("Could not find Invoice with provided Invoice.id")
    invoice.is_paid = is_paid
    db.commit()
    return invoice


def get_num_due_soon(db: sa.orm.Session, user_id: str) -> int:
    return (
        db.query(func.count(Invoice.id))
        .filter_by(user_id=user_id, is_paid=False)
        .filter(Invoice.due_date > datetime.utcnow())
        .scalar()
        or 0
    )


def get_num_overdue(db: sa.orm.Session, user_id: str) -> int:
    return (
        db.query(func.count(Invoice.id))
        .filter_by(user_id=user_id, is_paid=False)
        .filter(Invoice.due_date < datetime.utcnow())
        .scalar()
        or 0
    )


def get_num_paid(db: sa.orm.Session, user_id: str) -> int:
    return db.query(func.count(Invoice.id)).filter_by(user_id=user_id, is_paid=True).scalar() or 0


def get_invoice_links_by_category_name(db: sa.orm.Session, name: str, user_id: str) -> List[CategoryInvoiceAssociation]:
    category = db.query(Category).filter_by(name=name, user_id=user_id).first()
    if not category:
        return []
    return category.invoice_links


def get_category_by_name(db: sa.orm.Session, name: str, user_id: str) -> Optional[Category]:
    return db.query(Category).filter_by(user_id=user_id, name=name).first()


# TODO: Gotta do these upserts right
# TODO: user_id should translate to organization id
def ensure_category_by_name(db: sa.orm.Session, name: str, user_id: str) -> Category:
    existing = db.query(Category).filter_by(name=name, user_id=user_id).first()
    if existing:
        return existing

    new = Category(
        name=name,
        user_id=user_id,
    )

    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def get_category_link_by_invoice_id_and_name(
    db: sa.orm.Session, user_id: str, invoice_id: str, category_name: str
) -> Optional[CategoryInvoiceAssociation]:
    return (
        db.query(CategoryInvoiceAssociation)
        .join(Category, CategoryInvoiceAssociation.category_id == Category.id)
        .filter(CategoryInvoiceAssociation.invoice_id == invoice_id)
        .filter(Category.name == category_name)
        .first()
    )


def add_category_to_invoice(
    db: sa.orm.Session, user_id: str, invoice_id: str, category_name: str
) -> CategoryInvoiceAssociation:
    existing_link = get_category_link_by_invoice_id_and_name(db, user_id, invoice_id, category_name)
    if existing_link:
        return existing_link

    category = ensure_category_by_name(db, category_name, user_id)
    new_link = CategoryInvoiceAssociation(invoice_id=invoice_id, category_id=category.id)

    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


def remove_category_from_invoice(db: sa.orm.Session, user_id: str, invoice_id: str, category_name: str) -> None:
    # TODO: remove from category table if no associations?
    existing_link = get_category_link_by_invoice_id_and_name(db, user_id, invoice_id, category_name)
    if not existing_link:
        return existing_link

    db.delete(existing_link)
    db.commit()
