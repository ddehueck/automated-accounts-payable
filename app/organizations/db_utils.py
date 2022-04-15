from datetime import date, datetime
from typing import List, Optional
from unicodedata import name

import sqlalchemy as sa
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from app.db.models import Organization


def get_organization_by_id(db: Session, organization_id: str) -> Optional[Organization]:
    return db.query(Organization).filter_by(id=organization_id).one_or_none()
