"""Pydantic schemas for cash register entries and cash counts."""

from __future__ import annotations

from datetime import date as _Date
from decimal import Decimal as _Decimal

from pydantic import BaseModel, field_validator

from backend.models.cash import CashEntrySource, CashMovementType


class CashEntryCreate(BaseModel):
    date: _Date
    amount: _Decimal
    type: CashMovementType
    contact_id: int | None = None
    payment_id: int | None = None
    reference: str | None = None
    description: str = ""

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: _Decimal) -> _Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class CashEntryUpdate(BaseModel):
    date: _Date | None = None
    amount: _Decimal | None = None
    type: CashMovementType | None = None
    contact_id: int | None = None
    payment_id: int | None = None
    reference: str | None = None
    description: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: _Decimal | None) -> _Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("amount must be positive")
        return v


class CashEntryRead(BaseModel):
    id: int
    date: _Date
    amount: _Decimal
    type: CashMovementType
    contact_id: int | None
    payment_id: int | None
    reference: str | None
    description: str
    source: CashEntrySource
    balance_after: _Decimal
    is_system_opening: bool

    model_config = {"from_attributes": True}


class LinkedAccountingEntry(BaseModel):
    """Minimal accounting entry info returned in cash connection checks."""

    id: int
    account_number: str
    label: str
    debit: _Decimal
    credit: _Decimal

    model_config = {"from_attributes": True}


class CashEntryConnectionsRead(BaseModel):
    """Result of checking what is connected to a cash entry before deletion."""

    can_delete: bool
    blocking_reason: str | None = None
    accounting_entries: list[LinkedAccountingEntry] = []


class CashCountCreate(BaseModel):
    date: _Date
    count_100: int = 0
    count_50: int = 0
    count_20: int = 0
    count_10: int = 0
    count_5: int = 0
    count_2: int = 0
    count_1: int = 0
    count_cents_50: int = 0
    count_cents_20: int = 0
    count_cents_10: int = 0
    count_cents_5: int = 0
    count_cents_2: int = 0
    count_cents_1: int = 0
    notes: str | None = None

    @field_validator(
        "count_100",
        "count_50",
        "count_20",
        "count_10",
        "count_5",
        "count_2",
        "count_1",
        "count_cents_50",
        "count_cents_20",
        "count_cents_10",
        "count_cents_5",
        "count_cents_2",
        "count_cents_1",
        mode="before",
    )
    @classmethod
    def counts_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("count must be non-negative")
        return v


class CashCountRead(BaseModel):
    id: int
    date: _Date
    count_100: int
    count_50: int
    count_20: int
    count_10: int
    count_5: int
    count_2: int
    count_1: int
    count_cents_50: int
    count_cents_20: int
    count_cents_10: int
    count_cents_5: int
    count_cents_2: int
    count_cents_1: int
    total_counted: _Decimal
    balance_expected: _Decimal
    difference: _Decimal
    notes: str | None

    model_config = {"from_attributes": True}


class CashBalanceRead(BaseModel):
    balance: _Decimal
