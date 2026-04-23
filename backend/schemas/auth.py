"""Pydantic schemas for authentication endpoints."""

from datetime import datetime

from pydantic import BaseModel, field_validator

from backend.models.user import UserRole

PASSWORD_MIN_LENGTH = 8


def _validate_password_complexity(value: str) -> str:
    """Enforce password policy: min 8 chars, ≥ 1 ASCII uppercase, ≥ 1 ASCII digit."""
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if not any(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c in "0123456789" for c in value):
        raise ValueError("Password must contain at least one digit")
    return value


class OrmReadModel(BaseModel):
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.READONLY

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _validate_password_complexity(v)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores and hyphens allowed)")
        return v


class UserRead(OrmReadModel):
    id: int
    username: str
    email: str
    role: UserRole
    must_change_password: bool
    is_active: bool
    created_at: datetime


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class UserSelfUpdate(BaseModel):
    email: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _validate_password_complexity(v)


class UserPasswordReset(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _validate_password_complexity(v)
