from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.sql import desc, func

import app.db.models as db_models
from app.invoices.db_utils import query_invoices


def get_vendors_by_user(db: sa.orm.Session, user_id: int) -> List[db_models.Vendor]:
    return db.query(db_models.Vendor).filter_by(user_id=user_id).all()


def get_vendor_by_id(db: sa.orm.Session, id: str) -> Optional[db_models.Vendor]:
    return db.query(db_models.Vendor).filter_by(id=id).first()


def get_total_paid_by_vendor(db: sa.orm.Session, vendor_id: str) -> int:
    return db.query(func.sum(db_models.Invoice.amount_due)).filter_by(vendor_id=vendor_id, is_paid=True).scalar() or 0


def get_total_due_by_vendor(db: sa.orm.Session, vendor_id: str) -> int:
    return db.query(func.sum(db_models.Invoice.amount_due)).filter_by(vendor_id=vendor_id, is_paid=False).scalar() or 0


def get_total_invoice_count_by_vendor(db: sa.orm.Session, vendor_id: str) -> int:
    return db.query(func.count(db_models.Invoice.id)).filter_by(vendor_id=vendor_id).scalar() or 0


def get_invoice_last_added_on_by_vendor(db: sa.orm.Session, vendor_id: str) -> Optional[datetime]:
    res = (
        db.query(db_models.Invoice).filter_by(vendor_id=vendor_id).order_by(desc(db_models.Invoice.created_on)).first()
    )
    if not res:
        return None
    return res.created_on
