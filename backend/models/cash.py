"""Cash register and cash count models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base

_Date = date
_Decimal = Decimal


class CashMovementType(StrEnum):
    IN = "in"
    OUT = "out"


class CashRegister(Base):
    """Journal entry for the cash register."""

    __tablename__ = "cash_register"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[_Date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[_Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    type: Mapped[CashMovementType] = mapped_column(String(5), nullable=False, index=True)
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.id"), nullable=True, index=True
    )
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id"), nullable=True, index=True
    )
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    balance_after: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class CashCount(Base):
    """Physical cash counting record."""

    __tablename__ = "cash_counts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[_Date] = mapped_column(Date, nullable=False, index=True)
    # Billets
    count_100: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_50: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_20: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_10: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_5: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Pièces
    count_2: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_1: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_cents_50: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_cents_20: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_cents_10: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_cents_5: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_cents_2: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_cents_1: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Résultats
    total_counted: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    balance_expected: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    difference: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
