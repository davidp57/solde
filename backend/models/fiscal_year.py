"""Fiscal year model — accounting exercise management."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base

_Date = date


class FiscalYearStatus(StrEnum):
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


class FiscalYear(Base):
    """An accounting exercise (e.g. 2024-08-01 to 2025-07-31)."""

    __tablename__ = "fiscal_years"
    # Migration 0007 created a table-level UNIQUE constraint plus a plain index,
    # not a unique index: declared the same way so autogenerate sees no change.
    __table_args__ = (UniqueConstraint("name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    start_date: Mapped[_Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[_Date] = mapped_column(Date, nullable=False)
    status: Mapped[FiscalYearStatus] = mapped_column(
        String(10), nullable=False, default=FiscalYearStatus.OPEN, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
