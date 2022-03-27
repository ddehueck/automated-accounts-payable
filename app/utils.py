from datetime import datetime
from typing import Optional


def format_date_american(dt: datetime = None) -> Optional[str]:
    if not dt:
        return None
    return dt.strftime("%B %-d, %Y")
