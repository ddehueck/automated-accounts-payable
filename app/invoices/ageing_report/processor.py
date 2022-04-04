from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import sqlalchemy as sa

from app.invoices.ageing_report.models import AgeingReportInput, InvoiceGroup
from app.invoices.db_utils import get_invoices_by_user
from app.invoices.models import PublicInvoice


class AgeingReportProcessor:
    ageing_columns = ["0-30", "31-60", "61-90", "90+"]
    columns = ["Number", "Due Date"] + ageing_columns

    @classmethod
    def fetch_data(cls, db: sa.orm.Session, user_id: str) -> AgeingReportInput:
        all_invoices = get_invoices_by_user(
            db, user_id, due_after=datetime.today(), filter_by="due"
        )  # TODO: use timezone?

        vendor_name_invoice_list_map = defaultdict(list)
        for invoice in all_invoices:
            vendor_name_invoice_list_map[invoice.vendor_name].append(PublicInvoice.from_orm(invoice))

        data = AgeingReportInput(groups=[])
        for vendor_name, invoice_list in vendor_name_invoice_list_map.items():
            data.groups.append(InvoiceGroup(vendor_name=vendor_name, invoice_list=invoice_list))
        return data

    def apply(self, data: AgeingReportInput) -> pd.DataFrame:
        df = pd.DataFrame(columns=self.columns)

        # Add Vendor Sections
        for group in data.groups:
            df = df.append(
                pd.DataFrame([[group.vendor_name] + [" " for _ in range(len(self.columns) - 1)]], columns=self.columns)
            )

            invoice_rows = pd.DataFrame([self.invoice_to_row_dict(i) for i in group.invoice_list])
            sub_total_row = pd.DataFrame([self.gen_total_row_dict(group.invoice_list, title="subtotals:")])

            df = df.append(invoice_rows, sort=False)
            df = df.append(sub_total_row, sort=False)
            df = df.append(self.gen_empty_row_df(df), sort=False)

        # Add Final Total Section
        all_invoices = []
        for group in data.groups:
            all_invoices.extend(group.invoice_list)

        total_row = pd.DataFrame([self.gen_total_row_dict(all_invoices, title="Totals:")])
        df = df.append(total_row, sort=False)

        # Ensure we don't see any NaNs
        df = df.fillna("")
        return df

    def datetime_to_ageing_col(self, dt: datetime) -> str:
        time_from_now = dt - datetime.utcnow()
        if time_from_now <= timedelta(days=30):
            return "0-30"
        elif time_from_now <= timedelta(days=60):
            return "31-60"
        elif time_from_now <= timedelta(days=90):
            return "61-90"
        else:
            return "90+"

    def invoice_to_row_dict(self, invoice: PublicInvoice) -> Dict:
        row_dict = {c: 0 for c in self.ageing_columns}

        row_dict["Number"] = invoice.invoice_id
        row_dict["Due Date"] = invoice.due_date.strftime("%m/%d/%Y")

        bucket = self.datetime_to_ageing_col(invoice.due_date)
        row_dict[bucket] = f"{invoice.amount_due}"

        return row_dict

    def gen_total_row_dict(self, invoices: List[PublicInvoice], title: str = None) -> Dict:
        values = {c: [] for c in self.ageing_columns}
        for i in invoices:
            col = self.datetime_to_ageing_col(i.due_date)
            values[col].append(float(i.amount_due))

        row_dict = {c: f"{sum(values[c])}" for c in values}
        row_dict["Due Date"] = title if title else ""

        return row_dict

    def gen_empty_row_df(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame([[""] * len(df.columns)], columns=df.columns)
