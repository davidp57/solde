"""Application configuration — loaded from environment variables or .env file."""

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        if v == "":
            raise ValueError("jwt_secret_key must not be empty")
        if len(v) < 32:
            raise ValueError("jwt_secret_key must be at least 32 characters long")
        return v

    @model_validator(mode="after")
    def set_default_jwt_for_dev(self) -> "Settings":
        """Allow running without JWT secret in test/dev by using a safe default."""
        return self


def get_settings() -> Settings:
    """Return application settings singleton."""
    return _settings


# Module-level singleton — overridden in tests via dependency injection
_settings = Settings(jwt_secret_key="dev-secret-key-change-this-in-production-please")
