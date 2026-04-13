"""Fiscal year model — accounting exercise management."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, String, func
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

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    start_date: Mapped[_Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[_Date] = mapped_column(Date, nullable=False)
    status: Mapped[FiscalYearStatus] = mapped_column(
        String(10), nullable=False, default=FiscalYearStatus.OPEN, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
