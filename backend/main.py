"""FastAPI application entry point."""

import logging
import logging.config
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

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

# Paths exempt from the must-change-password gate
_PASSWORD_GATE_EXEMPT = frozenset(
    {
        "/api/auth/login",
        "/api/auth/refresh",
        "/api/auth/me",
        "/api/auth/me/change-password",
    }
)


class MustChangePasswordMiddleware(BaseHTTPMiddleware):
    """Block API access (403) when the JWT carries ``mcp=True`` (must change password).

    Only ``/api/auth/`` endpoints needed for the password change flow are allowed through.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path.rstrip("/")

        # Only gate API requests that are not in the exempt set
        if path.startswith("/api/") and path not in _PASSWORD_GATE_EXEMPT:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                from backend.services.auth import decode_access_token

                payload = decode_access_token(token)
                if payload and payload.get("mcp") is True:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Password change required before accessing this resource",
                        },
                    )

        return await call_next(request)


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

    app.add_middleware(MustChangePasswordMiddleware)

    # CORS — use CORS_ALLOWED_ORIGINS in production; falls back to ["*"] in debug mode
    _cors_origins = cfg.cors_allowed_origins or (["*"] if cfg.debug else [])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[misc]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not cfg.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        return response

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
