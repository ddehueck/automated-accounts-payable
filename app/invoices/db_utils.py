from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from app.db.models import Invoice

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
    return db.query(func.count(Invoice.id)).filter_by(user_id=user_id, is_paid=False).filter(Invoice.due_date > datetime.utcnow()).scalar() or 0


def get_num_overdue(db: sa.orm.Session, user_id: str) -> int:
    return db.query(func.count(Invoice.id)).filter_by(user_id=user_id, is_paid=False).filter(Invoice.due_date < datetime.utcnow()).scalar() or 0

    
def get_num_paid(db: sa.orm.Session, user_id: str) -> int:
    return db.query(func.count(Invoice.id)).filter_by(user_id=user_id, is_paid=True).scalar() or 0