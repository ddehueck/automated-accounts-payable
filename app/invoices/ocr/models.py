from datetime import datetime
from decimal import Decimal
from typing import Optional

import dateutil.parser as date_parser
from price_parser import Price
from pydantic import BaseModel, Field


class RawInvoiceBody(BaseModel):
    total_due: str = Field(None, alias="TOTAL")
    invoice_number: str = Field(None, alias="INVOICE_RECEIPT_ID")
    due_date: str = Field(None, alias="DUE_DATE")
    ambiguous_date: str = Field(None, alias="INVOICE_RECEIPT_DATE", description="Field that will capture a date. Fallback for when due date is not found.")
    vendor_name: str = Field(None, alias="VENDOR_NAME")

    def is_complete_parse(self) -> bool:
        return None not in self.dict().values()

    @property
    def formatted_total_due(self) -> Optional[Decimal]:
        price = Price.fromstring(self.total_due)
        return price.amount

    @property
    def formatted_currency(self) -> Optional[str]:
        price = Price.fromstring(self.total_due)
        return price.currency

    @property
    def formatted_due_date(self) -> Optional[datetime]:
        if self.due_date:
            return date_parser.parse(self.due_date)

        if self.ambiguous_date:
            return date_parser.parse(self.ambiguous_date)

        return None

    @property
    def formatted_vendor_name(self) -> Optional[str]:
        return " ".join(self.vendor_name.split())
