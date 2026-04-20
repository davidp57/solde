"""Pydantic schemas for contacts."""

from datetime import date as date_value
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, field_validator

from backend.models.contact import ContactType


class ContactWriteBase(BaseModel):
    type: ContactType
    nom: str
    prenom: str | None = None
    email: EmailStr | None = None
    telephone: str | None = None
    adresse: str | None = None
    notes: str | None = None

    @field_validator("nom")
    @classmethod
    def nom_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("nom must not be empty")
        return v.strip()


class ContactCreate(ContactWriteBase):
    pass


class ContactUpdate(BaseModel):
    """All fields optional for partial update."""

    type: ContactType | None = None
    nom: str | None = None
    prenom: str | None = None
    email: EmailStr | None = None
    telephone: str | None = None
    adresse: str | None = None
    notes: str | None = None
    is_active: bool | None = None

    @field_validator("nom")
    @classmethod
    def nom_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("nom must not be empty")
        return v.strip() if v else v


class ContactRead(BaseModel):
    id: int
    type: ContactType
    nom: str
    prenom: str | None = None
    email: str | None = None
    telephone: str | None = None
    adresse: str | None = None
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactInvoiceSummary(BaseModel):
    id: int
    number: str
    type: str
    date: date_value
    due_date: date_value | None
    status: str
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal

    model_config = {"from_attributes": True}


class ContactPaymentSummary(BaseModel):
    id: int
    date: date_value
    amount: Decimal
    method: str
    invoice_number: str | None

    model_config = {"from_attributes": True}


class ContactHistory(BaseModel):
    contact: ContactRead
    invoices: list[ContactInvoiceSummary]
    payments: list[ContactPaymentSummary]
    total_invoiced: Decimal
    total_paid: Decimal
    total_due: Decimal
