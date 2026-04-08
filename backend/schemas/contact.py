"""Pydantic schemas for contacts."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from backend.models.contact import ContactType


class ContactBase(BaseModel):
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


class ContactCreate(ContactBase):
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


class ContactRead(ContactBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
