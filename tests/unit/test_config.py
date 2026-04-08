"""Tests for application configuration settings."""

import pytest
from pydantic import ValidationError

_VALID_SECRET = "a-valid-secret-key-that-is-long-enough-for-jwt"


def test_default_fiscal_year_start_month() -> None:
    """Fiscal year defaults to starting in August (month 8)."""
    from backend.config import Settings

    settings = Settings(jwt_secret_key=_VALID_SECRET)
    assert settings.fiscal_year_start_month == 8


def test_fiscal_year_start_month_valid_range() -> None:
    """Fiscal year start month must be between 1 and 12."""
    from backend.config import Settings

    with pytest.raises(ValidationError):
        Settings(fiscal_year_start_month=0)

    with pytest.raises(ValidationError):
        Settings(fiscal_year_start_month=13)


def test_database_url_defaults_to_data_folder() -> None:
    """Default DB URL points to data folder."""
    from backend.config import Settings

    settings = Settings(jwt_secret_key=_VALID_SECRET)
    assert "data/" in settings.database_url
    assert settings.database_url.endswith(".db")


def test_jwt_secret_key_required() -> None:
    """JWT secret key must be set (no empty string)."""
    from backend.config import Settings

    with pytest.raises(ValidationError):
        Settings(jwt_secret_key="")


def test_jwt_secret_key_has_minimum_length() -> None:
    """JWT secret key must be at least 32 characters."""
    from backend.config import Settings

    with pytest.raises(ValidationError):
        Settings(jwt_secret_key="short")


def test_smtp_settings_optional() -> None:
    """SMTP settings are optional (can be None for dev)."""
    from backend.config import Settings

    settings = Settings(jwt_secret_key=_VALID_SECRET)
    assert settings.smtp_host is None or isinstance(settings.smtp_host, str)


def test_app_name() -> None:
    """App name is Solde."""
    from backend.config import Settings

    settings = Settings(jwt_secret_key=_VALID_SECRET)
    assert settings.app_name == "Solde"
