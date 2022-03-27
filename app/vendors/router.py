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

from .db_utils import get_vendors_by_user

router = APIRouter()


@router.get("/vendors", response_class=HTMLResponse)
async def get_dashboard(request: Request, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        vendors = get_vendors_by_user(db, user_id)

    return template_response("./vendors/vendors.html", {"request": request, "vendors": jsonable_encoder(vendors)})
