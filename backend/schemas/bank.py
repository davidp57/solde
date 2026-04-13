"""Pydantic schemas for bank transactions and deposit slips."""

from __future__ import annotations

from datetime import date as _Date
from decimal import Decimal as _Decimal

from pydantic import BaseModel, field_validator

from backend.models.bank import BankTransactionSource, DepositType


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

    model_config = {"from_attributes": True}


class BankTransactionUpdate(BaseModel):
    reconciled: bool | None = None
    reconciled_with: str | None = None
    reference: str | None = None
    description: str | None = None


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
    payment_ids: list[int] = []

    model_config = {"from_attributes": True}


class BankBalanceRead(BaseModel):
    balance: _Decimal
