"""Reversible import run models for prepared operations and effects."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ImportRunStatus(StrEnum):
    PREPARED = "prepared"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_REVERTED = "partially_reverted"
    REVERTED = "reverted"


class ImportOperationDecision(StrEnum):
    APPLY = "apply"
    IGNORE = "ignore"
    BLOCK = "block"


class ImportOperationStatus(StrEnum):
    PREPARED = "prepared"
    IGNORED = "ignored"
    BLOCKED = "blocked"
    APPLIED = "applied"
    UNDONE = "undone"
    FAILED = "failed"


class ImportEffectAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ImportEffectStatus(StrEnum):
    APPLIED = "applied"
    UNDONE = "undone"


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    import_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[ImportRunStatus] = mapped_column(String(30), nullable=False, index=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comparison_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    comparison_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    preview_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    operations: Mapped[list[ImportOperation]] = relationship(
        "ImportOperation",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ImportOperation.position",
    )


class ImportOperation(Base):
    __tablename__ = "import_operations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    operation_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_sheet: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_row_numbers_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[ImportOperationDecision] = mapped_column(
        String(20), nullable=False, index=True
    )
    status: Mapped[ImportOperationStatus] = mapped_column(String(20), nullable=False, index=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    run: Mapped[ImportRun] = relationship("ImportRun", back_populates="operations")
    effects: Mapped[list[ImportEffect]] = relationship(
        "ImportEffect",
        back_populates="operation",
        cascade="all, delete-orphan",
        order_by="ImportEffect.position",
    )


class ImportEffect(Base):
    __tablename__ = "import_effects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    operation_id: Mapped[int] = mapped_column(
        ForeignKey("import_operations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    action: Mapped[ImportEffectAction] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    entity_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    after_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[ImportEffectStatus] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    operation: Mapped[ImportOperation] = relationship("ImportOperation", back_populates="effects")
