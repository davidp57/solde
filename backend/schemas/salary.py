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
    # CDD breakdown components (optional)
    brut_declared: Decimal | None = None
    conges_payes: Decimal | None = None
    precarite: Decimal | None = None
    notes: str | None = None

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("month must be in YYYY-MM format")
        return v

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("hours must be non-negative")
        if v > 744:
            raise ValueError("hours cannot exceed 744 (31 days × 24 hours)")
        return v

    @field_validator(
        "gross",
        "employee_charges",
        "employer_charges",
        "tax",
        "net_pay",
        "brut_declared",
        "conges_payes",
        "precarite",
    )
    @classmethod
    def validate_non_negative(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("value must be non-negative")
        return v


class SalaryUpdate(BaseModel):
    hours: Decimal | None = None
    gross: Decimal | None = None
    employee_charges: Decimal | None = None
    employer_charges: Decimal | None = None
    tax: Decimal | None = None
    net_pay: Decimal | None = None
    brut_declared: Decimal | None = None
    conges_payes: Decimal | None = None
    precarite: Decimal | None = None
    notes: str | None = None

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            if v < 0:
                raise ValueError("hours must be non-negative")
            if v > 744:
                raise ValueError("hours cannot exceed 744 (31 days × 24 hours)")
        return v

    @field_validator(
        "gross",
        "employee_charges",
        "employer_charges",
        "tax",
        "net_pay",
        "brut_declared",
        "conges_payes",
        "precarite",
    )
    @classmethod
    def validate_non_negative(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("value must be non-negative")
        return v


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
    brut_declared: Decimal | None
    conges_payes: Decimal | None
    precarite: Decimal | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SalaryPreviousRead(BaseModel):
    """Pre-fill data for 'copy previous salary' — only pre-CEA fields."""

    employee_id: int
    hours: Decimal
    gross: Decimal
    brut_declared: Decimal | None
    conges_payes: Decimal | None
    precarite: Decimal | None


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


class WorkforceCostRow(BaseModel):
    """One row in the consolidated workforce cost view (salaries + AE invoices)."""

    month: str
    person_id: int
    person_name: str
    person_type: str  # "CDI", "CDD", "AE"
    hours: Decimal | None
    amount: Decimal  # gross for employees, invoice total for AE
    total_cost: Decimal  # gross + employer charges for employees, invoice total for AE
    hourly_cost: Decimal | None  # total_cost / hours if hours > 0
