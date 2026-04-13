"""Application configuration — loaded from environment variables or .env file."""

import sys

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
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///data/solde.db"

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # Fiscal year (month number: 8 = August)
    fiscal_year_start_month: int = 8

    # Association info (shown on invoices)
    association_name: str = "Mon Association"
    association_address: str = ""
    association_siret: str = ""
    association_logo_path: str = ""

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

    # SMTP (optional)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True

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


def get_settings() -> Settings:
    """Return application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


_settings: Settings | None = None
