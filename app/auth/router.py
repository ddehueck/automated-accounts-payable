import imp
from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND

import app.db.models as db_models
from app.auth.models import UserRoleEnum
from app.config import config as global_config
from app.db.session import SessionLocal
from app.emails.utils import send_reset_pswd_email
from app.frontend.templates import template_response
from app.users.db_utils import get_user_by_id

from .db_utils import create_reset_pwd_token
from .session_utils import UserSession, clear_session, set_session
from .utils import hash_pswd, requires_authentication, verify_pswd

router = APIRouter()


# @router.get("/register", response_class=HTMLResponse)
# async def get_register(request: Request):
#     return template_response("./auth/register.html", {"request": request})


# TODO: Proper redirects
@router.post("/register", response_class=RedirectResponse)
async def post_register(
    request: Request,
    name: str = Form(...),
    company_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(..., min_length=6),
):
    with SessionLocal() as db:
        existing_user = db.query(db_models.User).filter_by(email=email).first()
        if existing_user:
            params = urlencode({"error": "This email has already been registered."})
            return RedirectResponse(f"/landing?{params}", status_code=HTTP_302_FOUND)

        # Create a new organization and add user to it.
        # TODO: Allow users to merge with an exisiting organization
        new_organization = db_models.Organization(name=company_name)
        db.add(new_organization)
        db.flush()
        db.refresh(new_organization)

        new_user = db_models.User(
            name=name, email=email, password_hash=hash_pswd(password), organization_id=new_organization.id
        )
        db.add(new_user)
        db.flush()
        db.refresh(new_user)
        db.commit()

        set_session(request, UserSession.from_user(new_user))
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
            params = urlencode({"error": "Password or email is incorrect."})
            return RedirectResponse(f"/login?{params}", status_code=HTTP_302_FOUND)

        if not verify_pswd(password, existing_user.password_hash):
            params = urlencode({"error": "Password or email is incorrect."})
            return RedirectResponse(f"/login?{params}", status_code=HTTP_302_FOUND)

        set_session(request, UserSession.from_user(existing_user))

    if existing_user.role == UserRoleEnum.admin:
        return RedirectResponse("/admin/home", status_code=HTTP_302_FOUND)
    return RedirectResponse("/", status_code=HTTP_302_FOUND)


@router.post("/settings/reset-password", response_class=RedirectResponse)
def settings_reset_password(user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        token: db_models.ResetPasswordToken = create_reset_pwd_token(db, user_id)

        reset_pswd_link = f"{global_config.base_domain}/reset-password?token={token.token}"
        send_reset_pswd_email(user.email, reset_pswd_link)

    return RedirectResponse(
        "/settings/account?message=Email has been sent with reset password link.", status_code=HTTP_302_FOUND
    )


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
