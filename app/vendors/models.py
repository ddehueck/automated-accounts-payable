from datetime import datetime
from locale import currency
from typing import List, Optional

import sqlalchemy as sa
from pydantic import BaseModel

from app.db.models import Vendor
from app.utils import format_date_american

from .db_utils import (get_invoice_last_added_on_by_vendor,
                       get_total_due_by_vendor,
                       get_total_invoice_count_by_vendor,
                       get_total_paid_by_vendor)


class PublicVendorView(BaseModel):
    id: str
    name: str
    aliases: List[str] = []
    contact_email: str = None

    total_paid: str
    total_due: str
    currency: str
    total_invoice_count: str

    last_added_on: Optional[str] = None
    created_on: str
    updated_on: str = None

    @classmethod
    def load(cls, db: sa.orm.Session, vendor: Vendor) -> "PublicVendorView":
        total_due = get_total_due_by_vendor(db, vendor.id)
        total_paid = get_total_paid_by_vendor(db, vendor.id)
        total_invoice_count = get_total_invoice_count_by_vendor(db, vendor.id)
        last_added_on = get_invoice_last_added_on_by_vendor(db, vendor.id)

        # TODO: Allow for multiple currencies
        return cls(
            currency="$",
            total_due=total_due,
            total_paid=total_paid,
            total_invoice_count=total_invoice_count,
            last_added_on=format_date_american(last_added_on),
            id=vendor.id,
            name=vendor.name,
            aliases=vendor.aliases,
            contact_email=vendor.contact_email,
            created_on=format_date_american(vendor.created_on),
            updated_on=format_date_american(vendor.updated_on),
        )
