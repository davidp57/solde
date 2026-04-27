"""Pydantic schemas for accounting rules."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from backend.models.accounting_rule import EntrySide, TriggerType


class AccountingRuleEntrySchema(BaseModel):
    id: int
    account_number: str
    side: EntrySide
    description_template: str

    model_config = {"from_attributes": True}


class AccountingRuleEntryCreate(BaseModel):
    account_number: str
    side: EntrySide
    description_template: str = "{{label}}"


class AccountingRuleRead(BaseModel):
    id: int
    name: str
    trigger_type: TriggerType
    is_active: bool
    priority: int
    description: str | None
    entries: list[AccountingRuleEntrySchema]

    model_config = {"from_attributes": True}


class AccountingRuleCreate(BaseModel):
    name: str
    trigger_type: TriggerType
    is_active: bool = True
    priority: int = 10
    description: str | None = None
    entries: list[AccountingRuleEntryCreate] = []


class AccountingRuleUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    description: str | None = None
    entries: list[AccountingRuleEntryCreate] | None = None


class RulePreviewRequest(BaseModel):
    amount: Decimal
    label: str = "Libellé exemple"
    entry_date: date | None = None


class RulePreviewEntry(BaseModel):
    account_number: str
    label: str
    debit: Decimal
    credit: Decimal
