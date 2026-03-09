from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth import router as auth_router
from app.api.dev_pages import router as dev_pages_router
from app.api.form_templates import router as form_templates_router
from app.api.ingest import router as ingest_router
from app.api.public_pages import router as public_pages_router
from app.api.review_admin import router as review_admin_router
from app.api.review_forms import router as review_forms_router
from app.api.user_access_admin import router as user_access_admin_router
from app.db import close_db_pool, init_db_pool
from app.logging_config import configure_logging
from app.settings import get_settings

configure_logging()
settings = get_settings()

app = FastAPI(title="QC Coversheets Ingest API", version="0.1.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie=settings.session_cookie_name,
    https_only=settings.session_https_only,
    same_site=settings.session_same_site,
    max_age=settings.session_max_age_seconds,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(form_templates_router)
app.include_router(review_admin_router)
app.include_router(review_forms_router)
app.include_router(user_access_admin_router)
app.include_router(public_pages_router)
app.include_router(dev_pages_router)


@app.exception_handler(HTTPException)
async def redirect_unauthenticated_html(request: Request, exc: HTTPException):
    if exc.status_code == 401 and request.method in {"GET", "HEAD"}:
        accept = request.headers.get("accept", "")
        dest = request.headers.get("sec-fetch-dest", "")
        if "text/html" in accept or dest == "document":
            return RedirectResponse(url="/", status_code=303)
    return await http_exception_handler(request, exc)


@app.middleware("http")
async def disable_cache_for_protected_html(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/dev/", "/admin/")):
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("text/html"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
    return response


@app.on_event("startup")
async def startup() -> None:
    await init_db_pool()


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_db_pool()
