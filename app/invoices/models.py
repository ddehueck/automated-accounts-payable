from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.db.models import Invoice
from app.invoices.ocr.models import RawInvoiceBody


class CreateInvoice(BaseModel):
    user_id: str

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
