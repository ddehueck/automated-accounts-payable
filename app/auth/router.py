from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND

import app.db.models as db_models
from app.db.session import SessionLocal
from app.frontend.templates import template_response

from .session_utils import UserSession, clear_session, set_session
from .utils import hash_pswd, requires_authentication, verify_pswd

router = APIRouter()


@router.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    return template_response("./auth/register.html", {"request": request})


# TODO: Proper redirects
@router.post("/register", response_class=RedirectResponse)
async def post_register(request: Request, email: str = Form(...), password: str = Form(..., min_length=6)):
    with SessionLocal() as db:
        existing_user = db.query(db_models.User).filter_by(email=email).first()
        if existing_user:
            return RedirectResponse("/register?error=true", status_code=HTTP_302_FOUND)

        new_user = db_models.User(email=email, password_hash=hash_pswd(password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    set_session(request, UserSession(user_id=new_user.id))
    return RedirectResponse("/", status_code=HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return template_response("./auth/login.html", {"request": request})


# TODO: Proper redirects
@router.post("/login", response_class=RedirectResponse)
async def post_login(request: Request, email: str = Form(...), password: str = Form(...)):
    with SessionLocal() as db:
        existing_user: db_models.User = db.query(db_models.User).filter_by(email=email).first()
        if not existing_user:
            return RedirectResponse("/login?error=true", status_code=HTTP_302_FOUND)

        if not verify_pswd(password, existing_user.password_hash):
            return RedirectResponse("/login?error=true", status_code=HTTP_302_FOUND)

    set_session(request, UserSession(user_id=existing_user.id, projects=projects))
    return RedirectResponse("/", status_code=HTTP_302_FOUND)


@router.get("/reset-password", response_class=HTMLResponse)
async def get_reset_password(request: Request, token: str):
    return template_response("./auth/reset-password.html", {"request": request, "token": token})


@router.post("/reset-password", response_class=RedirectResponse)
async def post_reset_password(token: str, password: str = Form(..., min_length=6)):
    with SessionLocal() as db:
        ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
        existing_token = (
            db.query(db_models.ResetPasswordToken)
            .filter_by(token=token)
            .filter(db_models.ResetPasswordToken.created_on >= ten_min_ago)
            .first()
        )
        if not existing_token:
            raise HTTPException(400, "Bad Request.")

        user: db_models.User = db.query(db_models.User).filter_by(id=existing_token.user_id).first()
        if not user:
            raise HTTPException(400, "Bad Request.")

        user.password_hash = hash_pswd(password)
        db.commit()
    return RedirectResponse("/login", status_code=HTTP_302_FOUND)


@router.get("/logout", response_class=RedirectResponse)
async def post_register(request: Request, user_id: str = Depends(requires_authentication)):
    clear_session(request)
    return RedirectResponse("/", status_code=HTTP_302_FOUND)
