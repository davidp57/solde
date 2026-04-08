"""Pydantic schemas for accounting accounts."""

from pydantic import BaseModel, field_validator

from backend.models.accounting_account import AccountType


class AccountingAccountBase(BaseModel):
    number: str
    label: str
    type: AccountType
    parent_number: str | None = None
    description: str | None = None

    @field_validator("number")
    @classmethod
    def validate_number(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("number must not be empty")
        if not v.isdigit():
            raise ValueError("number must contain only digits")
        return v

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("label must not be empty")
        return v.strip()


class AccountingAccountCreate(AccountingAccountBase):
    pass


class AccountingAccountUpdate(BaseModel):
    label: str | None = None
    type: AccountType | None = None
    parent_number: str | None = None
    description: str | None = None
    is_active: bool | None = None

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("label must not be empty")
        return v.strip() if v else v


class AccountingAccountRead(AccountingAccountBase):
    id: int
    is_default: bool
    is_active: bool

    model_config = {"from_attributes": True}
