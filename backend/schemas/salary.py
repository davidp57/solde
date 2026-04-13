"""Pydantic schemas for salaries."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class SalaryCreate(BaseModel):
    employee_id: int
    month: str  # YYYY-MM
    hours: Decimal = Decimal("0")
    gross: Decimal
    employee_charges: Decimal = Decimal("0")
    employer_charges: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    net_pay: Decimal
    notes: str | None = None

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("month must be in YYYY-MM format")
        return v


class SalaryUpdate(BaseModel):
    hours: Decimal | None = None
    gross: Decimal | None = None
    employee_charges: Decimal | None = None
    employer_charges: Decimal | None = None
    tax: Decimal | None = None
    net_pay: Decimal | None = None
    notes: str | None = None


class SalaryRead(BaseModel):
    id: int
    employee_id: int
    employee_name: str | None = None  # denormalized for display
    month: str
    hours: Decimal
    gross: Decimal
    employee_charges: Decimal
    employer_charges: Decimal
    tax: Decimal
    net_pay: Decimal
    total_cost: Decimal
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SalarySummaryRow(BaseModel):
    """Aggregated salary row for a given month."""

    month: str
    total_gross: Decimal
    total_employee_charges: Decimal
    total_employer_charges: Decimal
    total_tax: Decimal
    total_net_pay: Decimal
    total_cost: Decimal
    count: int
