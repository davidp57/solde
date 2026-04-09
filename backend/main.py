"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.database import init_db
from backend.routers import (
    accounting_account,
    accounting_entry,
    accounting_rule,
    auth,
    bank,
    cash,
    contact,
    dashboard,
    excel_import,
    fiscal_year,
    invoice,
    payment,
    salary,
    settings,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: initialise DB on startup."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    cfg = get_settings()

    app = FastAPI(
        title=cfg.app_name,
        version=cfg.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS — in production this should be restricted to the frontend origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if cfg.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routers
    app.include_router(auth.router, prefix="/api")
    app.include_router(contact.router, prefix="/api")
    app.include_router(accounting_account.router, prefix="/api")
    app.include_router(accounting_entry.router, prefix="/api")
    app.include_router(accounting_rule.router, prefix="/api")
    app.include_router(fiscal_year.router, prefix="/api")
    app.include_router(invoice.router, prefix="/api")
    app.include_router(payment.router, prefix="/api")
    app.include_router(cash.router, prefix="/api")
    app.include_router(bank.router, prefix="/api")
    app.include_router(salary.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(excel_import.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")

    # Serve Vue.js frontend static files (built output)
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app


app = create_app()
