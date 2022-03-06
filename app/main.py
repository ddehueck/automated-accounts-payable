from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .auth.router import router as auth_router
from .config import config as global_config
from .invoices.router import router as invoices_router
from .marketing.router import router as marketing_router
from .payments.router import router as payments_router
from .users.router import router as users_router

if global_config.in_deployment:
    app = FastAPI(docs_url=None)
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
