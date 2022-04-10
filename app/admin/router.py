import imp

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND

from app.admin.models import AdminUserView
from app.auth.utils import admin_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response

router = APIRouter(
    dependencies=[Depends(admin_authentication)],
)


@router.get("/admin/home", response_class=HTMLResponse)
async def get_admin_home(request: Request):
    return template_response("./admin/admin-home.html", {"request": request})
