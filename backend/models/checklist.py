"""Monthly bookkeeping checklist — session and per-step state.

A *session* is one run of the checklist for one accounting period.  Its steps
are not stored as data: the list lives in ``backend/services/checklist_steps.py``
and is versioned with the application, the way a manufacturer's checklist is.
Only the *state* of each step is persisted here.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ChecklistPeriodType(StrEnum):
    #: One session per calendar month. A yearly closing checklist would add a
    #: value here and a second step list — no schema change.
    MONTHLY = "monthly"


class ChecklistSessionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class ChecklistSession(Base):
    __tablename__ = "checklist_sessions"
    __table_args__ = (UniqueConstraint("period_type", "period", name="uq_checklist_period"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    period_type: Mapped[ChecklistPeriodType] = mapped_column(
        String(10), nullable=False, default=ChecklistPeriodType.MONTHLY
    )
    #: The period being worked on, not the day the session is held: "2026-09".
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    status: Mapped[ChecklistSessionStatus] = mapped_column(
        String(10), nullable=False, default=ChecklistSessionStatus.OPEN, index=True
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    opened_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class ChecklistStepState(Base):
    __tablename__ = "checklist_step_states"
    __table_args__ = (UniqueConstraint("session_id", "step_key", name="uq_checklist_step"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("checklist_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_key: Mapped[str] = mapped_column(String(50), nullable=False)
    checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    checked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #: Left unchecked when the previous session was closed, and brought forward.
    carried_over: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
