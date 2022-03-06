from datetime import datetime
from typing import List

from pydantic import BaseModel


class User(BaseModel):
    id: str
    organization_id: str = None
    email: str
    password_hash: str
    paid_plan: str = None
    stripe_session_id: str = None
    created_on: datetime
    updated_on: datetime = None

    class Config:
        orm_mode = True
