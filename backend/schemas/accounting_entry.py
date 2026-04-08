"""Pydantic schemas for accounting entries."""

from __future__ import annotations

from datetime import date as _Date
from decimal import Decimal as _Decimal

from pydantic import BaseModel, field_validator

from backend.models.accounting_entry import EntrySourceType


class AccountingEntryRead(BaseModel):
    id: int
    entry_number: str
    date: _Date
    account_number: str
    label: str
    debit: _Decimal
    credit: _Decimal
    fiscal_year_id: int | None
    source_type: EntrySourceType | None
    source_id: int | None

    model_config = {"from_attributes": True}


class ManualEntryCreate(BaseModel):
    """Create a balanced pair of debit + credit entries manually."""

    date: _Date
    debit_account: str
    credit_account: str
    amount: _Decimal
    label: str
    fiscal_year_id: int | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: _Decimal) -> _Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


# ---------------------------------------------------------------------------
# Report schemas
# ---------------------------------------------------------------------------


class BalanceRow(BaseModel):
    account_number: str
    account_label: str
    account_type: str
    total_debit: _Decimal
    total_credit: _Decimal
    solde: _Decimal  # positive = debit balance, negative = credit balance


class LedgerEntry(BaseModel):
    id: int
    entry_number: str
    date: _Date
    label: str
    debit: _Decimal
    credit: _Decimal
    running_balance: _Decimal


class LedgerRead(BaseModel):
    account_number: str
    account_label: str
    entries: list[LedgerEntry]
    opening_balance: _Decimal
    closing_balance: _Decimal


class ResultatRead(BaseModel):
    total_charges: _Decimal
    total_produits: _Decimal
    resultat: _Decimal  # positive = excédent, negative = déficit
    charges: list[BalanceRow]
    produits: list[BalanceRow]
