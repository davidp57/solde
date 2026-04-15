"""Pydantic schemas for application settings."""

from __future__ import annotations

from datetime import date as _Date
from decimal import Decimal as _Decimal

from pydantic import BaseModel, field_validator


class AppSettingsRead(BaseModel):
    """Settings returned by GET /api/settings.

    smtp_password is intentionally excluded for security.
    """

    association_name: str
    association_address: str
    association_siret: str
    association_logo_path: str
    fiscal_year_start_month: int

    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_from_email: str | None
    smtp_use_tls: bool

    model_config = {"from_attributes": True}


class AppSettingsUpdate(BaseModel):
    """Payload for PUT /api/settings — all fields optional (partial update)."""

    association_name: str | None = None
    association_address: str | None = None
    association_siret: str | None = None
    fiscal_year_start_month: int | None = None

    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool | None = None

    @field_validator("fiscal_year_start_month")
    @classmethod
    def validate_month(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 12:
            raise ValueError("fiscal_year_start_month must be between 1 and 12")
        return v

    @field_validator("smtp_port")
    @classmethod
    def validate_port(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 65535:
            raise ValueError("smtp_port must be between 1 and 65535")
        return v


class SystemOpeningRead(BaseModel):
    configured: bool
    date: _Date | None = None
    amount: _Decimal | None = None
    reference: str | None = None


class TreasurySystemOpeningRead(BaseModel):
    default_date: _Date | None = None
    bank: SystemOpeningRead
    cash: SystemOpeningRead


class SystemOpeningUpdate(BaseModel):
    date: _Date
    amount: _Decimal
    reference: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: _Decimal) -> _Decimal:
        if v == 0:
            raise ValueError("amount must not be zero")
        return v


class TreasurySystemOpeningUpdate(BaseModel):
    bank: SystemOpeningUpdate
    cash: SystemOpeningUpdate
