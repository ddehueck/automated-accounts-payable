from typing import Optional

import sqlalchemy as sa

import app.db.models as db_models


def get_vendors_by_user(db: sa.orm.Session, user_id: int) -> Optional[db_models.Vendor]:
    return db.query(db_models.Vendor).filter_by(user_id=user_id).all()
