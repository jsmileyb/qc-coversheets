from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.dev_pages import router as dev_pages_router
from app.api.form_templates import router as form_templates_router
from app.api.ingest import router as ingest_router
from app.api.review_admin import router as review_admin_router
from app.api.review_forms import router as review_forms_router
from app.db import close_db_pool, init_db_pool
from app.logging_config import configure_logging

configure_logging()

app = FastAPI(title="QC Coversheets Ingest API", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(ingest_router)
app.include_router(form_templates_router)
app.include_router(review_admin_router)
app.include_router(review_forms_router)
app.include_router(dev_pages_router)


@app.on_event("startup")
async def startup() -> None:
    await init_db_pool()


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_db_pool()
