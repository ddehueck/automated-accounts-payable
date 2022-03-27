from email.mime import image
from urllib import request

import fitz
import ulid
from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from loguru import logger as log
from pydantic import BaseModel
from result import Result
from sqlalchemy import desc
from starlette.status import HTTP_302_FOUND

from app.auth.utils import requires_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.invoices.ocr.textract import InvoiceImageProcessor, textract_client

from .db_utils import (add_category_to_invoice, get_invoice_by_id,
                       get_invoices_by_user, remove_category_from_invoice,
                       save_invoice, update_paid_status_invoice)
from .models import CreateInvoice, PublicInvoice
from .s3_utils import upload_image_obj

router = APIRouter()
processor = InvoiceImageProcessor(textract_client)


@router.get("/inbox", response_class=HTMLResponse)
async def get_home(
    request: Request,
    user_id: str = Depends(requires_authentication),
    filter_by: str = None,
    order_by: str = "due_date",
    desc: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    with SessionLocal() as db:
        invoices = get_invoices_by_user(
            db, user_id, filter_by=filter_by, order_by=order_by, limit=limit, offset=offset, desc=desc
        )
    invoices = {i.id: PublicInvoice.from_orm(i).dict() for i in invoices}
    return template_response("./invoices/inbox.html", {"request": request, "invoices": invoices})


@router.get("/invoices/{invoice_id}")
async def get_single_invoice(request: Request, invoice_id: str, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        invoice = get_invoice_by_id(db, invoice_id)
        invoice = PublicInvoice.from_orm(invoice)
    return template_response("./invoices/single-invoice.html", {"request": request, "data": jsonable_encoder(invoice)})


@router.post("/invoices/{invoice_id}")
async def post_single_invoice(invoice_id: str, paid: bool, user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        update_paid_status_invoice(db, invoice_id, is_paid=paid)
    return RedirectResponse(f"/home#{invoice_id}", status_code=HTTP_302_FOUND)


@router.get("/upload-invoice", response_class=HTMLResponse)
async def get_register(request: Request):
    return template_response("./invoices/upload.html", {"request": request})


@router.post("/upload-invoice")
async def post_upload_invoice(file: UploadFile = File(...), user_id: str = Depends(requires_authentication)):
    allow_list = ("image/png", "image/jpeg", "image/jpg", "application/pdf")
    if file.content_type not in allow_list:
        raise HTTPException(422, detail="File must be a .png, .jpg, or .pdf")

    file_data = await file.read()
    if file.content_type == "application/pdf":
        doc = fitz.open(stream=file_data, filetype="pdf")
        page = doc.load_page(0)  # number of page
        file_data = page.get_pixmap().tobytes(output="PNG")

    parse_result: Result = processor.apply(file_data)
    if not parse_result.is_ok:
        return parse_result.err()

    raw_parse = parse_result.ok()
    formatted_invoice = CreateInvoice.from_raw_parse(user_id, raw_parse)

    # Upload image to S3
    extension = file.content_type.split("/")[1]
    # TODO: return image uri
    formatted_invoice.image_uri = upload_image_obj(file_data, f"{str(ulid.ulid())}", extension)

    with SessionLocal() as db:
        # TODO: Use file data to upsert based on image md5 hash
        db_invoice = save_invoice(db, formatted_invoice)

    return RedirectResponse(f"/home?order_by=created_on&desc=True&index={db_invoice.id}", status_code=HTTP_302_FOUND)

# API routes - no redirects - pure actions

class AddCategoryBody(BaseModel):
    category_name: str

@router.put("/invoices/{invoice_id}/categories")
async def put_single_invoice(invoice_id: str, body: AddCategoryBody, user_id: str = Depends(requires_authentication)):
    # Add categories
    with SessionLocal() as db:
        add_category_to_invoice(db, user_id, invoice_id, body.category_name)
    return Response(status_code=201)


@router.delete("/invoices/{invoice_id}/categories")
async def put_single_invoice(invoice_id: str, category_name: str, user_id: str = Depends(requires_authentication)):
    # Add categories
    with SessionLocal() as db:
        remove_category_from_invoice(db, user_id, invoice_id, category_name)
    return Response(status_code=200)
