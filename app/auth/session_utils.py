import json
from typing import List

from fastapi import Request
from pydantic import BaseModel


class UserSession(BaseModel):
    user_id: str = None


def set_session(req: Request, data: UserSession) -> None:
    """Modifies Request.session in place"""
    jsonable_dict: dict = json.loads(data.json())
    for k, v in jsonable_dict.items():
        req.session[k] = v


def clear_session(req: Request) -> None:
    """Modifies Request.session in place"""
    set_session(req, UserSession())
