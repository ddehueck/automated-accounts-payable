from typing import List

from pydantic import BaseModel

from app.invoices.models import PublicInvoice


class InvoiceGroup(BaseModel):
    vendor_name: str
    invoice_list: List[PublicInvoice]


class AgeingReportInput(BaseModel):
    groups: List[InvoiceGroup]
