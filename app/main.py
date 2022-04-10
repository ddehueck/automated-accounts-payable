import rollbar
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from rollbar.contrib.fastapi import ReporterMiddleware as RollbarMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_302_FOUND

from app.auth.utils import optional_authentication

from .admin.router import router as admin_router
from .auth.router import router as auth_router
from .config import config as global_config
from .invoices.router import router as invoices_router
from .marketing.router import router as marketing_router
from .payments.router import router as payments_router
from .users.router import router as users_router
from .vendors.router import router as vendors_router

if global_config.in_deployment:
    app = FastAPI(docs_url=None)
    # Deployment specific middleware
    rollbar.init(global_config.rollbar_key, environment="production")
    app.add_middleware(RollbarMiddleware)
else:
    app = FastAPI()

app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

app.add_middleware(SessionMiddleware, secret_key=global_config.session_secret)
app.add_middleware(CORSMiddleware)

app.include_router(auth_router)
app.include_router(invoices_router)
app.include_router(marketing_router)
app.include_router(payments_router)
app.include_router(users_router)
app.include_router(vendors_router)
app.include_router(admin_router)


global_router = APIRouter()


@global_router.get("/health")
def get_health():
    return True


@global_router.get("/", response_class=RedirectResponse)
def get_index(user_id: str = Depends(optional_authentication)):
    if user_id:
        return RedirectResponse("/inbox", status_code=HTTP_302_FOUND)
    return RedirectResponse("/landing", status_code=HTTP_302_FOUND)


app.include_router(global_router)
