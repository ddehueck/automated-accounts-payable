from typing import Optional

import sqlalchemy as sa

import app.db.models as db_models
from app.users.db_utils import get_user_by_id

from .models import PaymentPlanEnum


def update_user_payment_plan(
    db: sa.orm.Session, uid: int, plan: PaymentPlanEnum, stripe_session_id: str
) -> Optional[db_models.User]:
    user: db_models.User = get_user_by_id(db, uid)
    if not user:
        return None

    user.paid_plan = plan
    user.stripe_session_id = stripe_session_id

    db.commit()
    db.refresh(user)
    return user
