from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette.status import HTTP_302_FOUND

import app.invoices.db_utils as invoice_utils
from app.auth.utils import requires_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.users.db_utils import get_user_by_id

from .models import User

router = APIRouter()


class DashboardData(BaseModel):
    num_due_soon: int
    num_overdue: int
    num_paid: int


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        num_due_soon = invoice_utils.get_num_due_soon(db, user_id)
        num_overdue = invoice_utils.get_num_overdue(db, user_id)
        num_paid = invoice_utils.get_num_paid(db, user_id)

    data = DashboardData(num_due_soon=num_due_soon, num_overdue=num_overdue, num_paid=num_paid)

    return template_response("./users/dashboard.html", {"request": request, "data": jsonable_encoder(data)})


@router.get("/settings/account", response_class=HTMLResponse)
async def get_settings_account(request: Request, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        user = User.from_orm(user)
    return template_response("./users/account-settings.html", {"request": request, "user": jsonable_encoder(user)})
