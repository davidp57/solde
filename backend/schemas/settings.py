"""Pydantic schemas for application settings."""

from __future__ import annotations

from datetime import date as _Date
from datetime import datetime as _Datetime
from decimal import Decimal as _Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from backend.models.import_log import ImportLogType


class AppSettingsRead(BaseModel):
    """Settings returned by GET /api/settings.

    smtp_password is intentionally excluded for security.
    """

    association_name: str
    association_address: str
    association_siret: str
    association_logo_path: str
    fiscal_year_start_month: int
    default_invoice_due_days: int | None
    client_invoice_seq_digits: int

    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_from_email: str | None
    smtp_use_tls: bool
    smtp_bcc: str | None

    model_config = {"from_attributes": True}


class AppSettingsUpdate(BaseModel):
    """Payload for PUT /api/settings — all fields optional (partial update)."""

    association_name: str | None = None
    association_address: str | None = None
    association_siret: str | None = None
    fiscal_year_start_month: int | None = None
    default_invoice_due_days: int | None = None
    client_invoice_seq_digits: int | None = None

    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool | None = None
    smtp_bcc: str | None = None

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

    @field_validator("default_invoice_due_days")
    @classmethod
    def validate_default_invoice_due_days(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= 365:
            raise ValueError("default_invoice_due_days must be between 0 and 365")
        return v

    @field_validator("client_invoice_seq_digits")
    @classmethod
    def validate_client_invoice_seq_digits(cls, v: int | None) -> int | None:
        if v is not None and not 2 <= v <= 6:
            raise ValueError("client_invoice_seq_digits must be between 2 and 6")
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


class SelectiveResetRequest(BaseModel):
    import_type: ImportLogType
    fiscal_year_id: int


class SelectiveResetPreviewRead(BaseModel):
    import_type: ImportLogType
    fiscal_year_id: int
    fiscal_year_name: str
    fiscal_year_start_date: _Date
    fiscal_year_end_date: _Date
    matched_import_logs: int
    matched_import_runs: int
    root_objects: dict[str, int]
    derived_objects: dict[str, int]
    delete_plan: dict[str, int]


# ---------------------------------------------------------------------------
# System info (BIZ-108)
# ---------------------------------------------------------------------------


class SystemInfoRead(BaseModel):
    """Read-only system information for the supervision screen."""

    app_version: str
    db_size_bytes: int
    started_at: _Datetime
    log_file: str


class BackupCreate(BaseModel):
    """Payload for POST /api/settings/backup."""

    label: str | None = None

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 50:
            raise ValueError("Label must be at most 50 characters")
        return v or None


class BackupFileRead(BaseModel):
    """Metadata for a single backup file."""

    filename: str
    size_bytes: int
    created_at: _Datetime
    label: str | None = None


class LogEntryRead(BaseModel):
    """A single parsed log line."""

    timestamp: str
    level: str
    logger: str
    message: str


# ---------------------------------------------------------------------------
# Audit log (BIZ-109)
# ---------------------------------------------------------------------------


class AuditLogRead(BaseModel):
    """A single audit log entry."""

    id: int
    action: str
    actor_id: int | None
    actor_username: str | None
    target_type: str | None
    target_id: int | None
    detail: dict[str, Any] | None
    created_at: _Datetime

    model_config = {"from_attributes": True}
