"""Invoice and InvoiceLine models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

# Type aliases to avoid name shadowing within class bodies
_Date = date
_Decimal = Decimal


class InvoiceType(StrEnum):
    CLIENT = "client"
    FOURNISSEUR = "fournisseur"


class InvoiceLabel(StrEnum):
    CS = "cs"
    ADHESION = "a"
    CS_ADHESION = "cs+a"
    GENERAL = "general"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    DISPUTED = "disputed"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    type: Mapped[InvoiceType] = mapped_column(String(20), nullable=False, index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False, index=True)
    date: Mapped[_Date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[_Date | None] = mapped_column(Date, nullable=True)
    label: Mapped[InvoiceLabel | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_amount: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    paid_amount: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20), nullable=False, default=InvoiceStatus.DRAFT, index=True
    )
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    lines: Mapped[list[InvoiceLine]] = relationship(
        "InvoiceLine", back_populates="invoice", cascade="all, delete-orphan"
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[_Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("1"))
    unit_price: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    amount: Mapped[_Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="lines")
