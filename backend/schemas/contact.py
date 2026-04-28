"""Pydantic schemas for contacts."""

from datetime import date as date_value
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.models.contact import ContactType, ContractType


class ContactWriteBase(BaseModel):
    type: ContactType
    nom: str = Field(max_length=100)
    prenom: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    telephone: str | None = Field(default=None, max_length=30)
    adresse: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)
    contract_type: ContractType | None = None
    base_gross: Decimal | None = Field(default=None, ge=0)
    base_hours: Decimal | None = Field(default=None, ge=0)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    is_contractor: bool = False
    child_first_name: str | None = Field(default=None, max_length=100)
    child_last_name: str | None = Field(default=None, max_length=100)
    other_parent_first_name: str | None = Field(default=None, max_length=100)
    other_parent_last_name: str | None = Field(default=None, max_length=100)

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
    nom: str | None = Field(default=None, max_length=100)
    prenom: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    telephone: str | None = Field(default=None, max_length=30)
    adresse: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None
    contract_type: ContractType | None = None
    base_gross: Decimal | None = Field(default=None, ge=0)
    base_hours: Decimal | None = Field(default=None, ge=0)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    is_contractor: bool | None = None
    child_first_name: str | None = Field(default=None, max_length=100)
    child_last_name: str | None = Field(default=None, max_length=100)
    other_parent_first_name: str | None = Field(default=None, max_length=100)
    other_parent_last_name: str | None = Field(default=None, max_length=100)

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
    contract_type: ContractType | None = None
    base_gross: Decimal | None = None
    base_hours: Decimal | None = None
    hourly_rate: Decimal | None = None
    is_contractor: bool
    child_first_name: str | None = None
    child_last_name: str | None = None
    other_parent_first_name: str | None = None
    other_parent_last_name: str | None = None
    created_at: datetime
    updated_at: datetime
    last_invoice_ref: str | None = None
    last_invoice_date: date_value | None = None

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


class ContactEmailImportRow(BaseModel):
    nom: str
    email: EmailStr

    @field_validator("nom")
    @classmethod
    def nom_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("nom must not be empty")
        return v.strip()

    @field_validator("email", mode="before")
    @classmethod
    def email_strip(cls, v: str) -> str:
        return v.strip()


class ContactEmailImportResult(BaseModel):
    rows_processed: int
    updated: int
    not_found: int
    already_has_email: int
    updated_indices: list[int] = []
    not_found_indices: list[int] = []
    already_has_email_indices: list[int] = []
