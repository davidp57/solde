"""Pydantic schemas for invoices and invoice lines."""

from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator, model_validator

from backend.models.invoice import InvoiceLabel, InvoiceLineType, InvoiceStatus, InvoiceType


class InvoiceLineBase(BaseModel):
    description: str
    line_type: InvoiceLineType | None = None
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be empty")
        return v.strip()

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v

class InvoiceLineCreate(InvoiceLineBase):
    pass


class InvoiceLineRead(InvoiceLineBase):
    id: int
    invoice_id: int
    amount: Decimal

    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    type: InvoiceType
    contact_id: int
    date: datetime.date
    due_date: datetime.date | None = None
    label: InvoiceLabel | None = None
    description: str | None = None
    reference: str | None = None


class InvoiceCreate(InvoiceBase):
    lines: list[InvoiceLineCreate] = []
    total_amount: Decimal | None = None  # required for supplier invoices without lines

    @field_validator("total_amount")
    @classmethod
    def total_amount_non_negative(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("total_amount must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_client_total(self) -> InvoiceCreate:
        if self.type != InvoiceType.CLIENT or not self.lines:
            return self
        computed_total = sum(
            (line.quantity * line.unit_price for line in self.lines),
            start=Decimal("0"),
        )
        if computed_total < 0:
            raise ValueError("client invoice total must not be negative")
        return self


class InvoiceUpdate(BaseModel):
    """All fields optional for partial update."""

    contact_id: int | None = None
    date: datetime.date | None = None
    due_date: datetime.date | None = None
    label: InvoiceLabel | None = None
    description: str | None = None
    reference: str | None = None
    lines: list[InvoiceLineCreate] | None = None
    total_amount: Decimal | None = None

    @model_validator(mode="after")
    def validate_client_total(self) -> InvoiceUpdate:
        if self.lines is None:
            return self
        computed_total = sum(
            (line.quantity * line.unit_price for line in self.lines),
            start=Decimal("0"),
        )
        if computed_total < 0:
            raise ValueError("client invoice total must not be negative")
        return self


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


class InvoiceRead(InvoiceBase):
    id: int
    number: str
    total_amount: Decimal
    paid_amount: Decimal
    status: InvoiceStatus
    pdf_path: str | None = None
    file_path: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    lines: list[InvoiceLineRead] = []

    model_config = {"from_attributes": True}
