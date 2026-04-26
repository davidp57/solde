"""FastAPI application entry point."""

import logging
import logging.config
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

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

logger = logging.getLogger("backend")

_INTERNAL_ERROR_DETAIL = (
    "An unexpected error occurred. Please try again or contact the administrator."
)


class UnhandledExceptionMiddleware:
    """Catch-all ASGI middleware for unhandled exceptions.

    Returns a structured JSON 500 response instead of an HTML traceback,
    and logs the full exception server-side for debugging.
    Must be added **after** all other middleware so it sits outermost
    (just inside Starlette's built-in ServerErrorMiddleware).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            request = Request(scope)
            logger.error(
                "Unhandled exception on %s %s: %s",
                request.method,
                request.url.path,
                exc,
                exc_info=exc,
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": _INTERNAL_ERROR_DETAIL,
                    "code": "INTERNAL_SERVER_ERROR",
                },
            )
            await response(scope, receive, send)


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
        "/api/auth/logout",
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
    swagger_enabled = cfg.swagger_enabled or cfg.debug

    _tags: list[dict[str, str]] = [
        {"name": "health", "description": "Health check endpoint."},
        {"name": "auth", "description": "Authentication — login, token refresh, profile."},
        {"name": "contacts", "description": "Clients and suppliers — CRUD and email import."},
        {
            "name": "accounting",
            "description": (
                "Accounting — chart of accounts, journal entries, rules and fiscal years."
            ),
        },
        {
            "name": "invoices",
            "description": "Client invoices — creation, status, PDF generation and email delivery.",
        },
        {"name": "payments", "description": "Payment recording and reconciliation."},
        {"name": "cash", "description": "Cash in/out operations."},
        {"name": "bank", "description": "Bank transactions and statement import."},
        {"name": "salaries", "description": "Monthly salary records."},
        {"name": "dashboard", "description": "Summary statistics and fiscal-year dashboard."},
        {
            "name": "import",
            "description": "Excel historical import — preview, validation and commit.",
        },
        {"name": "settings", "description": "Application settings."},
    ]

    app = FastAPI(
        title=cfg.app_name,
        version=cfg.app_version,
        openapi_tags=_tags,
        docs_url="/api/docs" if swagger_enabled else None,
        redoc_url="/api/redoc" if swagger_enabled else None,
        openapi_url="/api/openapi.json" if swagger_enabled else None,
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
    async def add_security_headers(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not cfg.debug:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
            if not swagger_enabled:
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

    # Health check (no auth required, used by Docker HEALTHCHECK)
    @app.get("/api/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

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
        # SPA fallback: serve the exact file if it exists (assets, favicon…),
        # otherwise return index.html so Vue Router handles client-side routing.
        # This prevents 404 on hard-refresh (Ctrl+F5) for any Vue route.
        # index.html is never cached (no-store) so that after a Docker rebuild the
        # browser always fetches the latest version with up-to-date chunk hashes,
        # preventing "error loading dynamically imported module" on stale hashes.
        # Hashed assets (/assets/*) get an immutable long-lived cache entry.
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> Response:  # noqa: RUF029
            file_path = frontend_dist / full_path
            if file_path.is_file() and full_path != "index.html":
                response = FileResponse(str(file_path))
                if full_path.startswith("assets/"):
                    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
                return response
            # SPA route fallback or direct /index.html request — never cache
            response = FileResponse(str(frontend_dist / "index.html"))
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            return response

    # --- Global exception handler: added LAST so it's outermost user middleware ---
    app.add_middleware(UnhandledExceptionMiddleware)

    return app


app = create_app()
