from fastapi import APIRouter, Depends, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette.status import HTTP_302_FOUND

import app.invoices.db_utils as invoice_utils
from app.auth.utils import requires_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.invoices.db_utils import query_invoices
from app.invoices.models import PublicInvoice

from .db_utils import get_vendor_by_id, get_vendors_by_user, update_vendor_contact_email
from .models import PublicVendorView

router = APIRouter()


@router.get("/vendors", response_class=HTMLResponse)
async def get_vendors(request: Request, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        vendors = get_vendors_by_user(db, user_id)
        vendors = [PublicVendorView.load(db, v) for v in vendors]
    return template_response("./vendors/vendors.html", {"request": request, "vendors": jsonable_encoder(vendors)})


@router.get("/vendors/{vendor_id}", response_class=HTMLResponse)
async def get_single_vendor(request: Request, vendor_id: str, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        vendor = get_vendor_by_id(db, vendor_id)
        if not vendor:
            return Response("404 Vendor not found.", status_code=404)
        vendor = PublicVendorView.load(db, vendor)
        invoices = [
            PublicInvoice.from_orm(i) for i in query_invoices(db, vendor_id=vendor_id, order_by="created_on", desc=True)
        ]

    return template_response(
        "./vendors/single-vendor.html",
        {"request": request, "vendor": jsonable_encoder(vendor), "invoices": jsonable_encoder(invoices)},
    )


# API ROUTES


class VendorUpdateBody(BaseModel):
    contact_email: str

@router.put("/vendors/{vendor_id}")
async def update_vendor(vendor_id: str, body: VendorUpdateBody, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        update_vendor_contact_email(db, vendor_id, body.contact_email)
    return Response(status_code=200)