from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AdminUserView(BaseModel):
    id: str
    company_name: str
    email: str
    paid_plan: str
    created_on: datetime
    last_payment_made: Optional[datetime]
