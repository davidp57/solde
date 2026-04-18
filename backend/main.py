"""FastAPI application entry point."""

import logging
import logging.config
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

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(LOG_DIR / "solde.log"),
                "maxBytes": 5 * 1024 * 1024,  # 5 MB
                "backupCount": 3,
                "encoding": "utf-8",
                "formatter": "default",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "backend": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["file"],
                "level": "INFO" if get_settings().debug else "WARNING",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    }
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
