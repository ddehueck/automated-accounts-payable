from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from pydantic import BaseModel

from app.db.models import User
from app.payments.models import PaymentPlanEnum
from app.users.db_utils import get_user_by_id
from app.utils import format_date_american


class AdminUserView(BaseModel):
    id: str
    company_name: Optional[str] = None
    email: str
    paid_plan: Optional[str] = PaymentPlanEnum.free
    created_on: str
    last_payment_made: Optional[str] = None

    @classmethod
    def load_from_db(cls, user: User) -> "AdminUserView":
        return AdminUserView(
            id=user.id,
            company_name=user.organization.name if user.organization else None,
            email=user.email,
            paid_plan=user.paid_plan,
            created_on=format_date_american(user.created_on),
            last_payment_made=None,
        )
