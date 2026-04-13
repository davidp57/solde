"""Pydantic schemas for payments."""

from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from backend.models.invoice import InvoiceType
from backend.models.payment import PaymentMethod


class PaymentBase(BaseModel):
    invoice_id: int
    contact_id: int
    amount: Decimal
    date: datetime.date
    method: PaymentMethod
    cheque_number: str | None = None
    reference: str | None = None
    notes: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    amount: Decimal | None = None
    date: datetime.date | None = None
    method: PaymentMethod | None = None
    cheque_number: str | None = None
    reference: str | None = None
    notes: str | None = None
    deposited: bool | None = None
    deposit_date: datetime.date | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("amount must be positive")
        return v


class PaymentRead(PaymentBase):
    id: int
    invoice_number: str | None = None
    invoice_type: InvoiceType | None = None
    deposited: bool
    deposit_date: datetime.date | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
