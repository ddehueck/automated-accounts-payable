from typing import Optional

import sqlalchemy as sa

import app.db.models as db_models


def get_user_by_id(db: sa.orm.Session, user_id: int) -> Optional[db_models.User]:
    return db.query(db_models.User).filter_by(id=user_id).first()
