from datetime import datetime, timedelta
from decimal import Decimal
from typing import Union

import humanize
from pydantic import BaseModel, validator

from app.db.models import Invoice
from app.invoices.ocr.models import RawInvoiceBody


class CreateInvoice(BaseModel):
    user_id: str

    is_paid: bool = False
    vendor_name: str = None
    amount_due: Decimal = None
    currency: str = None
    due_date: datetime = None
    invoice_id: str = None

    raw_vendor_name: str = None
    raw_amount_due: str = None
    raw_due_date: str = None

    @classmethod
    def from_raw_parse(cls, user_id: str, raw: RawInvoiceBody) -> "CreateInvoice":
        return cls(
            user_id=user_id,
            vendor_name=raw.formatted_vendor_name,
            amount_due=raw.formatted_total_due,
            currency=raw.formatted_currency,
            due_date=raw.formatted_due_date,
            invoice_id=raw.invoice_number,
            raw_vendor_name=raw.vendor_name,
            raw_amount_due=raw.total_due,
            raw_due_date=raw.due_date,
        )

    def to_orm(self) -> Invoice:
        return Invoice(**self.dict())


class PublicInvoice(BaseModel):
    id: str
    is_paid: bool = None
    vendor_name: str = None
    amount_due: Decimal = None
    currency: str = None
    due_date: datetime = None
    invoice_id: str = None
    humanized_due_date: Union[str, datetime] = None

    @validator("humanized_due_date")
    def humanize_datetime(cls, v: datetime) -> str:
        if not isinstance(v, datetime):
            raise ValueError("Must pass datetime for humanized date")
        current_time = datetime.utcnow()
        delta: timedelta = current_time - v
        return humanize.naturaltime(delta)

    @classmethod
    def from_orm(cls, db_invoice: Invoice) -> "PublicInvoice":
        return cls(humanized_due_date=db_invoice.due_date, **db_invoice.__dict__)
