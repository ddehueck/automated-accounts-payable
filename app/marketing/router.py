from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND

from app.auth.utils import requires_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response

router = APIRouter()


@router.get("/landing", response_class=HTMLResponse)
async def get_landing(request: Request):
    return template_response("./marketing/landing.html", {"request": request})


@router.get("/how-it-works", response_class=HTMLResponse)
async def get_landing(request: Request):
    return template_response("./marketing/how-it-works.html", {"request": request})
