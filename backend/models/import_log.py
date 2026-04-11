"""Import log model for Excel import traceability and idempotence."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ImportLogType(StrEnum):
    GESTION = "gestion"
    COMPTABILITE = "comptabilite"


class ImportLogStatus(StrEnum):
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"


class ImportLog(Base):
    """Trace a single Excel import attempt identified by a file hash."""

    __tablename__ = "import_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    import_type: Mapped[ImportLogType] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[ImportLogStatus] = mapped_column(String(20), nullable=False, index=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
