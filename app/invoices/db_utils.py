import re
from datetime import date, datetime
from typing import List, Optional
from unicodedata import name

import sqlalchemy as sa
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from app.db.models import (AgingReport, Category, CategoryInvoiceAssociation,
                           Invoice, Vendor)

from .models import CreateInvoice


def get_invoice_by_id(db: Session, invoice_id: str) -> Optional[Invoice]:
    return db.query(Invoice).filter_by(id=invoice_id).first()


def ensure_vendor_by_name(db: sa.orm.Session, vendor_name: str, user_id: str) -> Vendor:
    # TODO: proper upsert? And need to set organization id.
    existing = db.query(Vendor).filter_by(name=vendor_name, user_id=user_id).first()
    if existing:
        return existing

    new = Vendor(
        name=vendor_name,
        user_id=user_id,
    )

    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def save_invoice(db: Session, invoice: CreateInvoice) -> Invoice:
    db_invoice = invoice.to_orm()
    db_vendor = ensure_vendor_by_name(db, db_invoice.vendor_name, invoice.user_id)

    db_invoice.vendor_id = db_vendor.id

    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


def query_invoices(
    db: Session,
    *,
    user_id: str = None,
    vendor_id: str = None,
    filter_by: str = None,
    order_by: str = "due_date",
    limit: int = 100,
    offset: int = 0,
    desc: bool = False,
    due_date: datetime = None,
    due_after: datetime = None,
    due_before: datetime = None,
) -> List[Invoice]:
    """Retrieves invoices from db

    Args:
        db (Session): SessionLocal object
        user_id (str): User to pull invoices from.
        vendor_id (str): Vendor to pull invoice from
        order_by (str, optional): Name of column to order by. Defaults to "due_date".
        desc (bool, optional): Indicates if results should be sorted in a desc fashion or not (i.e. asc). Defaults to False.
        limit (int, optional): Max number of results to be returned. Defaults to 100.
        offset (int, optional): Offset to allow for pagination. Defaults to 0.

    NOTE: Either one of or both of vendor_id and user_id must be provided

    Returns:
        List[Invoice]
    """
    if not user_id and not vendor_id:
        raise Exception("At least on of user_id and vendor_id must be provided")

    invoices_query = db.query(Invoice)

    if user_id:
        invoices_query = invoices_query.filter_by(user_id=user_id)
    if vendor_id:
        invoices_query = invoices_query.filter_by(vendor_id=vendor_id)

    if filter_by == "paid":
        invoices_query = invoices_query.filter_by(is_paid=True)
    elif filter_by == "due":
        invoices_query = invoices_query.filter_by(is_paid=False)
    elif filter_by == "all":
        # TODO Add enumerations
        pass

    if due_date:
        invoices_query = invoices_query.filter(Invoice.due_date >= due_date).filter(Invoice.due_date <= due_date)

    if due_after:
        invoices_query = invoices_query.filter(Invoice.due_date >= due_after)

    if due_before:
        invoices_query = invoices_query.filter(Invoice.due_date <= due_before)

    try:
        order_by_stmt = getattr(Invoice, order_by)
    except AttributeError as e:
        return []

    if desc:
        order_by_stmt = sa.desc(order_by_stmt)

    invoices_query = invoices_query.order_by(order_by_stmt)
    invoices_query = invoices_query.limit(limit).offset(offset)
    return invoices_query.all()


def get_invoices_by_user(
    db: Session,
    user_id: str,
    filter_by: str = None,
    order_by: str = "due_date",
    limit: int = 100,
    offset: int = 0,
    desc: bool = False,
    due_after: datetime = None,
) -> List[Invoice]:
    return query_invoices(
        db,
        user_id=user_id,
        filter_by=filter_by,
        order_by=order_by,
        limit=limit,
        offset=offset,
        desc=desc,
        due_after=due_after,
    )


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
def ensure_category_by_name(db: sa.orm.Session, name: str, user_id: str, commit: bool = True) -> Category:
    name = name.strip()

    existing = db.query(Category).filter_by(name=name, user_id=user_id).first()
    if existing:
        return existing

    new = Category(
        name=name,
        user_id=user_id,
    )

    db.add(new)

    if commit:
        db.commit()
    else:
        db.flush()

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

    # Remove existing links to ensure only one category
    db.query(CategoryInvoiceAssociation).filter_by(invoice_id=invoice_id).delete()

    category = ensure_category_by_name(db, category_name, user_id, commit=False)
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


def delete_invoice(db: sa.orm.Session, invoice_id: str) -> None:
    # Delete category links
    db.query(CategoryInvoiceAssociation).filter_by(invoice_id=invoice_id).delete()
    # Delete invoice
    db.query(Invoice).filter_by(id=invoice_id).delete()
    db.commit()


def get_aging_report_by_id(db: Session, report_id: str) -> Optional[AgingReport]:
    return db.query(AgingReport).filter_by(id=report_id).first()


def query_aging_reports(
    db: Session, user_id: str, *, order_by: str, limit: int = 100, offset: int = 0, desc: bool = False
) -> List[AgingReport]:

    query = db.query(AgingReport).filter_by(user_id=user_id)
    try:
        order_by_stmt = getattr(AgingReport, order_by)
    except AttributeError as e:
        return []

    if desc:
        order_by_stmt = sa.desc(order_by_stmt)

    query = query.order_by(order_by_stmt)
    query = query.limit(limit).offset(offset)
    return query.all()
