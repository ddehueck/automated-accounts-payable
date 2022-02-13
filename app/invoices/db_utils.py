from typing import List

import sqlalchemy as sa
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.db.models import Invoice

from .models import CreateInvoice


def save_invoice(db: Session, invoice: CreateInvoice) -> Invoice:
    db_model = invoice.to_orm()
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def get_invoices_by_user(
    db: Session, user_id: str, order_by: str = "due_date", limit: int = 100, offset: int = 0, desc: bool = False
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
    invoices = db.query(Invoice).filter_by(user_id=user_id).order_by(order_by_stmt).limit(limit).offset(offset).all()
    return invoices
