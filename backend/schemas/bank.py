"""Pydantic schemas for bank transactions and deposit slips."""

from __future__ import annotations

from datetime import date as _Date
from decimal import Decimal as _Decimal

from pydantic import BaseModel, Field, field_validator

from backend.models.bank import BankTransactionCategory, BankTransactionSource, DepositType


class BankTransactionCreate(BaseModel):
    date: _Date
    amount: _Decimal
    reference: str | None = None
    description: str = ""
    balance_after: _Decimal = _Decimal("0")
    source: BankTransactionSource = BankTransactionSource.MANUAL


class BankTransactionRead(BaseModel):
    id: int
    date: _Date
    amount: _Decimal
    reference: str | None
    description: str
    balance_after: _Decimal
    reconciled: bool
    reconciled_with: str | None
    source: BankTransactionSource
    detected_category: BankTransactionCategory
    payment_id: int | None
    payment_ids: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class BankTransactionUpdate(BaseModel):
    reconciled: bool | None = None
    reconciled_with: str | None = None
    reference: str | None = None
    description: str | None = None


class BankTransactionClientPaymentCreate(BaseModel):
    invoice_id: int


class BankTransactionClientPaymentAllocation(BaseModel):
    invoice_id: int
    amount: _Decimal

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: _Decimal) -> _Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class BankTransactionClientPaymentsCreate(BaseModel):
    allocations: list[BankTransactionClientPaymentAllocation]

    @field_validator("allocations")
    @classmethod
    def at_least_one_allocation(
        cls, v: list[BankTransactionClientPaymentAllocation]
    ) -> list[BankTransactionClientPaymentAllocation]:
        if not v:
            raise ValueError("at least one allocation is required")
        invoice_ids = [allocation.invoice_id for allocation in v]
        if len(invoice_ids) != len(set(invoice_ids)):
            raise ValueError("duplicate invoice allocations are not allowed")
        return v


class BankTransactionClientPaymentLink(BaseModel):
    payment_id: int


class BankTransactionClientPaymentLinks(BaseModel):
    payment_ids: list[int]

    @field_validator("payment_ids")
    @classmethod
    def at_least_one_payment(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("at least one payment is required")
        if len(v) != len(set(v)):
            raise ValueError("duplicate payments are not allowed")
        return v


class DepositCreate(BaseModel):
    date: _Date
    type: DepositType
    payment_ids: list[int]
    bank_reference: str | None = None
    notes: str | None = None

    @field_validator("payment_ids")
    @classmethod
    def at_least_one_payment(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("at least one payment is required")
        return v


class DepositRead(BaseModel):
    id: int
    date: _Date
    type: DepositType
    total_amount: _Decimal
    bank_reference: str | None
    notes: str | None
    confirmed: bool
    confirmed_date: _Date | None
    payment_ids: list[int] = []

    model_config = {"from_attributes": True}


class BankBalanceRead(BaseModel):
    balance: _Decimal
