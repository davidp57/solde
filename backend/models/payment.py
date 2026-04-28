"""Payment model — records a payment against an invoice."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base
from backend.models.types import DecimalType

_Date = date
_Decimal = Decimal


class PaymentMethod(StrEnum):
    ESPECES = "especes"
    CHEQUE = "cheque"
    VIREMENT = "virement"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False, index=True)
    amount: Mapped[_Decimal] = mapped_column(DecimalType(10, 2), nullable=False)
    date: Mapped[_Date] = mapped_column(Date, nullable=False, index=True)
    method: Mapped[PaymentMethod] = mapped_column(String(20), nullable=False, index=True)
    cheque_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deposited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    in_deposit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deposit_date: Mapped[_Date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
