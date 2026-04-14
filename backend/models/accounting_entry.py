"""Accounting entry model — double-entry journal lines."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base

_Date = date
_Decimal = Decimal


class EntrySourceType(StrEnum):
    GESTION = "gestion"
    INVOICE = "invoice"
    PAYMENT = "payment"
    DEPOSIT = "deposit"
    SALARY = "salary"
    MANUAL = "manual"
    CLOTURE = "cloture"


def build_entry_group_key(
    source_type: EntrySourceType | str | None,
    source_id: int | None,
) -> str | None:
    if source_type is None or source_id is None:
        return None
    source_value = source_type.value if isinstance(source_type, EntrySourceType) else source_type
    return f"{source_value}:{source_id}"


class AccountingEntry(Base):
    """A single debit or credit line in the accounting journal."""

    __tablename__ = "accounting_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entry_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date: Mapped[_Date] = mapped_column(Date, nullable=False, index=True)
    # Denormalized account number (no FK — history must survive account changes)
    account_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    label: Mapped[str] = mapped_column(Text, nullable=False, default="")
    debit: Mapped[_Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    credit: Mapped[_Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    fiscal_year_id: Mapped[int | None] = mapped_column(
        ForeignKey("fiscal_years.id"), nullable=True, index=True
    )
    source_type: Mapped[EntrySourceType | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    source_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    group_key: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
