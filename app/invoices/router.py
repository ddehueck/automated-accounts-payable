import fitz
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from result import Result
from sqlalchemy import desc

from app.auth.utils import requires_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.invoices.ocr.textract import InvoiceImageProcessor, textract_client

from .db_utils import get_invoices_by_user, save_invoice
from .models import CreateInvoice

router = APIRouter()
processor = InvoiceImageProcessor(textract_client)


@router.get("/home", response_class=HTMLResponse)
async def get_home(
    request: Request,
    user_id: str = Depends(requires_authentication),
    order_by: str = "due_date",
    desc: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    with SessionLocal() as db:
        invoices = get_invoices_by_user(db, user_id, order_by=order_by, limit=limit, offset=offset, desc=desc)

    invoices = [i.__dict__ for i in invoices]
    return template_response("./invoice-feed.html", {"request": request, "invoices": invoices})


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
        save_invoice(db, formatted_invoice)
    return formatted_invoice
