import fitz
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from result import Result
from sqlalchemy import desc
from starlette.status import HTTP_302_FOUND

from app.auth.utils import requires_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.invoices.ocr.textract import InvoiceImageProcessor, textract_client

from .db_utils import (get_invoices_by_user, save_invoice,
                       update_paid_status_invoice)
from .models import CreateInvoice, PublicInvoice

router = APIRouter()
processor = InvoiceImageProcessor(textract_client)


@router.get("/home", response_class=HTMLResponse)
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
    return template_response("./invoices/feed.html", {"request": request, "invoices": invoices})


@router.post("/invoices/{invoice_id}")
async def put_single_my_invoice(invoice_id: str, paid: bool, user_id: str = Depends(requires_authentication)):
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
    with SessionLocal() as db:
        db_invoice = save_invoice(db, formatted_invoice)
    return RedirectResponse(f"/home?order_by=created_on&desc=True&index={db_invoice.id}", status_code=HTTP_302_FOUND)
