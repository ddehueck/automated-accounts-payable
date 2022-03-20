from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND

from app.auth.utils import requires_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.users.db_utils import get_user_by_id

from .models import User

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request, user_id: str = Depends(requires_authentication)):
    return template_response("./users/dashboard.html", {"request": request})


@router.get("/settings/account", response_class=HTMLResponse)
async def get_settings_account(request: Request, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        user = User.from_orm(user)
    return template_response("./users/account-settings.html", {"request": request, "user": jsonable_encoder(user)})
