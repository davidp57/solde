"""Pydantic schemas for accounting entries."""

from __future__ import annotations

from datetime import date as _Date
from decimal import Decimal as _Decimal

from pydantic import BaseModel, field_validator

from backend.models.accounting_entry import EntrySourceType


class AccountingEntryRead(BaseModel):
    id: int
    entry_number: str
    group_key: str
    date: _Date
    account_number: str
    account_label: str | None = None
    label: str
    debit: _Decimal
    credit: _Decimal
    fiscal_year_id: int | None
    source_type: EntrySourceType | None
    source_id: int | None
    source_reference: str | None = None
    source_contact_name: str | None = None
    source_invoice_id: int | None = None
    source_invoice_type: str | None = None
    source_invoice_number: str | None = None
    editable: bool = False
    counterpart_entry_id: int | None = None
    counterpart_account_number: str | None = None
    counterpart_account_label: str | None = None

    model_config = {"from_attributes": True}


class AccountingEntryGroupRead(BaseModel):
    group_key: str
    date: _Date
    label: str
    fiscal_year_id: int | None
    source_type: EntrySourceType | None
    source_id: int | None
    source_reference: str | None = None
    source_contact_name: str | None = None
    source_invoice_id: int | None = None
    source_invoice_type: str | None = None
    source_invoice_number: str | None = None
    line_count: int
    total_debit: _Decimal
    total_credit: _Decimal
    account_numbers: list[str]
    editable: bool = False
    lines: list[AccountingEntryRead]


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


class ManualEntryUpdate(BaseModel):
    """Update a balanced debit + credit manual entry pair."""

    date: _Date
    debit_account: str
    credit_account: str
    amount: _Decimal
    label: str
    fiscal_year_id: int | None = None
    counterpart_entry_id: int

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


class BilanRead(BaseModel):
    """Simplified balance sheet — assets vs liabilities."""

    actif: list[BalanceRow]
    passif: list[BalanceRow]
    total_actif: _Decimal
    total_passif: _Decimal
    # Resultat of the period is included in passif (120000/129000)
    resultat: _Decimal
