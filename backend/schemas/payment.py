"""Pydantic schemas for payments."""

from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from backend.models.invoice import InvoiceType
from backend.models.payment import PaymentMethod


class PaymentBase(BaseModel):
    invoice_id: int
    contact_id: int
    amount: Decimal
    date: datetime.date
    method: PaymentMethod
    cheque_number: str | None = Field(default=None, max_length=50)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)

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
    cheque_number: str | None = Field(default=None, max_length=50)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)
    deposited: bool | None = None
    deposit_date: datetime.date | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("amount must be positive")
        return v


class PaymentCancelPreview(BaseModel):
    """Eligibility and side effects of cancelling a payment.

    ``reason_code`` is set only when ``can_cancel`` is False; the deposit fields
    describe what would happen to the slip the payment currently belongs to.
    """

    payment_id: int
    can_cancel: bool
    reason_code: str | None = None
    amount: Decimal
    date: datetime.date
    deposit_id: int | None = None
    deposit_date: datetime.date | None = None
    deposit_total_before: Decimal | None = None
    deposit_total_after: Decimal | None = None
    deposit_will_be_deleted: bool = False


class PaymentRead(PaymentBase):
    id: int
    invoice_number: str | None = None
    invoice_type: InvoiceType | None = None
    contact_name: str | None = None
    deposited: bool
    in_deposit: bool
    deposit_date: datetime.date | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
