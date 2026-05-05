"""Pydantic schemas for bank transactions and deposit slips."""

from __future__ import annotations

from datetime import date as _Date
from decimal import Decimal as _Decimal

from pydantic import BaseModel, Field, field_validator

from backend.models.bank import (
    BankAccountType,
    BankTransactionCategory,
    BankTransactionSource,
    DepositType,
)


class BankTransactionCreate(BaseModel):
    date: _Date
    amount: _Decimal
    reference: str | None = None
    description: str = ""
    balance_after: _Decimal = _Decimal("0")
    source: BankTransactionSource = BankTransactionSource.MANUAL
    bank_account: BankAccountType = BankAccountType.COURANT


class BankTransactionRead(BaseModel):
    id: int
    date: _Date
    amount: _Decimal
    reference: str | None
    description: str
    balance_after: _Decimal
    bank_account: BankAccountType
    reconciled: bool
    reconciled_with: str | None
    source: BankTransactionSource
    detected_category: BankTransactionCategory
    payment_id: int | None
    payment_ids: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class BankImportResult(BaseModel):
    created: list[BankTransactionRead]
    skipped: int


class BankTransactionUpdate(BaseModel):
    reconciled: bool | None = None
    reconciled_with: str | None = None
    reference: str | None = None
    description: str | None = None
    detected_category: BankTransactionCategory | None = None
    # Fields below are only applied when editing a manual transaction
    date: _Date | None = None
    amount: _Decimal | None = None
    bank_account: BankAccountType | None = None


class BankReconcileBulkRequest(BaseModel):
    ids: list[int]

    @field_validator("ids")
    @classmethod
    def ids_not_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("ids must not be empty")
        if len(v) != len(set(v)):
            raise ValueError("duplicate ids are not allowed")
        return v


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
    # For cheques deposits: list of payment IDs to include.
    # For especes deposits: leave empty — use total_amount instead.
    payment_ids: list[int] = []
    # For especes deposits: explicit amount (ignored for cheques, computed from payments).
    total_amount: _Decimal | None = None
    # Optional JSON-encoded denomination breakdown for cash deposits.
    # e.g. [{"value": 50, "count": 3}, {"value": 20, "count": 4}]
    denomination_details: str | None = None
    bank_reference: str | None = None
    notes: str | None = None

    @field_validator("payment_ids")
    @classmethod
    def payment_ids_no_duplicates(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("duplicate payment ids are not allowed")
        return v


class DepositUpdate(BaseModel):
    """Partial update of an unconfirmed deposit slip.

    Cheques deposit: supply ``payment_ids`` to replace the current selection
    (must remain non-empty and all cheque payments).
    Especes deposit: supply ``total_amount`` and/or ``denomination_details``.
    """

    payment_ids: list[int] | None = None
    total_amount: _Decimal | None = None
    denomination_details: str | None = None

    @field_validator("payment_ids")
    @classmethod
    def payment_ids_no_duplicates(cls, v: list[int] | None) -> list[int] | None:
        if v is not None and len(v) != len(set(v)):
            raise ValueError("duplicate payment ids are not allowed")
        return v


class DepositRead(BaseModel):
    id: int
    date: _Date
    type: DepositType
    total_amount: _Decimal
    bank_reference: str | None
    notes: str | None
    denomination_details: str | None
    confirmed: bool
    confirmed_date: _Date | None
    payment_ids: list[int] = []

    model_config = {"from_attributes": True}


class BankBalanceRead(BaseModel):
    balance: _Decimal
    balance_courant: _Decimal
    balance_epargne: _Decimal
