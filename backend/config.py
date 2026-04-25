"""Application configuration — loaded from environment variables or .env file."""

import sys
from functools import lru_cache
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    _SOLDE_VERSION = _pkg_version("solde")
except PackageNotFoundError:
    _SOLDE_VERSION = "0.0.0"

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_TEST_JWT_SECRET = "dev-secret-key-local-only-change-me-1234567890"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Solde"
    app_version: str = _SOLDE_VERSION
    debug: bool = False
    swagger_enabled: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///data/solde.db"

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # Fiscal year (month number: 8 = August)
    fiscal_year_start_month: int = 8

    # Bootstrap admin (created on first startup if no user exists)
    admin_username: str = "admin"
    admin_password: str = "changeme"
    admin_email: str = "admin@exemple.fr"

    # Temporary dev helpers
    enable_test_import_shortcuts: bool = False
    test_import_gestion_2024_path: str | None = None
    test_import_gestion_2025_path: str | None = None
    test_import_comptabilite_2024_path: str | None = None
    test_import_comptabilite_2025_path: str | None = None

    # CORS — allowed origins (comma-separated in env: CORS_ALLOWED_ORIGINS=http://a.com,http://b.com)
    # Empty list → ["*"] in debug mode, [] in production
    cors_allowed_origins: list[str] = []

    @field_validator("fiscal_year_start_month")
    @classmethod
    def validate_fiscal_year_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("fiscal_year_start_month must be between 1 and 12")
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if v != "" and len(v) < 32:
            raise ValueError("jwt_secret_key must be at least 32 characters long")
        return v

    @model_validator(mode="after")
    def ensure_jwt_secret(self) -> "Settings":
        """Require an explicit JWT secret outside explicit dev/test contexts."""
        if self.jwt_secret_key != "":
            return self

        if self.debug or "pytest" in sys.modules:
            self.jwt_secret_key = _DEV_TEST_JWT_SECRET
            return self

        raise ValueError("jwt_secret_key must be configured outside debug/test environments")


@lru_cache
def get_settings() -> Settings:
    """Return application settings singleton (cached after first call)."""
    return Settings()
