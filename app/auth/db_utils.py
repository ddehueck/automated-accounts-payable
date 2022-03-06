import sqlalchemy as sa

import app.db.models as db_models


def create_reset_pwd_token(db: sa.orm.Session, user_id: str) -> db_models.ResetPasswordToken:
    token = db_models.ResetPasswordToken(user_id=user_id)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token
