"""Tests for password complexity policy (BL-085).

Rules:
- Minimum 8 characters
- At least one uppercase letter
- At least one digit
"""

import pytest
from pydantic import ValidationError

from backend.schemas.auth import PasswordChangeRequest, UserCreate, UserPasswordReset

# ---------------------------------------------------------------------------
# Valid passwords — should be accepted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "password",
    [
        "Abcdefg1",  # exactly 8 chars, 1 upper, 1 digit
        "SecurePass99",  # long, mixed
        "A1xxxxxx",  # upper first, digit second
        "xxxxxxA1",  # upper + digit at end
        "P@ssw0rd!",  # special chars ok
    ],
)
def test_valid_passwords_accepted(password: str) -> None:
    schema = UserPasswordReset(new_password=password)
    assert schema.new_password == password


# ---------------------------------------------------------------------------
# Too short
# ---------------------------------------------------------------------------


def test_rejects_short_password() -> None:
    with pytest.raises(ValidationError, match="8 characters"):
        UserPasswordReset(new_password="Ab1xxxx")  # 7 chars


# ---------------------------------------------------------------------------
# Missing uppercase
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "password",
    [
        "abcdefg1",  # no uppercase
        "12345678",  # digits only
        "abcd1234",  # lower + digit, no upper
    ],
)
def test_rejects_password_without_uppercase(password: str) -> None:
    with pytest.raises(ValidationError, match="uppercase"):
        UserPasswordReset(new_password=password)


# ---------------------------------------------------------------------------
# Missing digit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "password",
    [
        "Abcdefgh",  # no digit
        "ABCDEFGH",  # all upper, no digit
        "Abcdefghij",  # long, no digit
    ],
)
def test_rejects_password_without_digit(password: str) -> None:
    with pytest.raises(ValidationError, match="digit"):
        UserPasswordReset(new_password=password)


# ---------------------------------------------------------------------------
# Applied on all 3 schemas
# ---------------------------------------------------------------------------


def test_user_create_validates_complexity() -> None:
    with pytest.raises(ValidationError, match="uppercase"):
        UserCreate(
            username="testuser",
            email="test@example.com",
            password="nouppercase1",
        )


def test_password_change_validates_complexity() -> None:
    with pytest.raises(ValidationError, match="digit"):
        PasswordChangeRequest(
            current_password="anything",
            new_password="NoDigitHere",
        )
