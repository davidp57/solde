"""Pydantic schemas for backup destinations and scheduling."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Backup destination
# ---------------------------------------------------------------------------


class BackupDestinationRead(BaseModel):
    id: int
    name: str
    type: str
    enabled: bool
    rclone_remote_name: str
    rclone_config: str | None
    target_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BackupDestinationCreate(BaseModel):
    name: str
    type: str  # local | smb | onedrive
    enabled: bool = True
    rclone_remote_name: str
    rclone_config: str | None = None  # JSON
    target_path: str = ""


class BackupDestinationUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    enabled: bool | None = None
    rclone_remote_name: str | None = None
    rclone_config: str | None = None
    target_path: str | None = None


# ---------------------------------------------------------------------------
# Backup schedule (stored in app_settings)
# ---------------------------------------------------------------------------


class BackupScheduleRead(BaseModel):
    enabled: bool
    schedule_type: str  # interval | cron
    interval_hours: int
    cron_expression: str | None
    include_uploads: bool
    notify_on_failure: bool

    model_config = {"from_attributes": True}

    @classmethod
    def from_settings(cls, s: Any) -> BackupScheduleRead:
        return cls(
            enabled=s.backup_enabled,
            schedule_type=s.backup_schedule_type,
            interval_hours=s.backup_interval_hours,
            cron_expression=s.backup_cron_expression,
            include_uploads=s.backup_include_uploads,
            notify_on_failure=s.backup_notify_on_failure,
        )


class BackupScheduleUpdate(BaseModel):
    enabled: bool | None = None
    schedule_type: str | None = None  # interval | cron
    interval_hours: int | None = None
    cron_expression: str | None = None
    include_uploads: bool | None = None
    notify_on_failure: bool | None = None


# ---------------------------------------------------------------------------
# Backup run status
# ---------------------------------------------------------------------------


class BackupDestinationResult(BaseModel):
    destination_id: int
    destination_name: str
    success: bool
    error: str | None = None


class BackupRunStatus(BaseModel):
    last_run_at: datetime | None
    last_run_status: str | None  # success | failure | None
    last_run_error: str | None = None
    destinations_results: list[BackupDestinationResult] = []


# ---------------------------------------------------------------------------
# Connection and restore test results
# ---------------------------------------------------------------------------


class BackupConnectionTestResult(BaseModel):
    success: bool
    message: str


class BackupRestoreTestResult(BaseModel):
    ok: bool
    integrity_check: str  # "ok" or SQLite integrity_check result
    tables_found: list[str] = []
    tables_missing: list[str] = []
    error: str | None = None


# ---------------------------------------------------------------------------
# OneDrive OAuth
# ---------------------------------------------------------------------------


class OneDriveOAuthStart(BaseModel):
    user_code: str        # e.g. "ABCD-1234" — user enters this at verification_uri
    verification_uri: str  # https://microsoft.com/devicelogin
    expires_in: int       # seconds until the code expires
    message: str          # human-readable instruction from Microsoft


class OneDriveOAuthStatus(BaseModel):
    done: bool
    token: str | None = None   # rclone_config JSON when done
    error: str | None = None
