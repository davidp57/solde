"""Tests for authentication service (JWT + password hashing)."""

import pytest
from datetime import timedelta


def test_hash_password_returns_hashed_value() -> None:
    """Password hashing produces a different string than the input."""
    from backend.services.auth import hash_password

    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"
    assert len(hashed) > 20


def test_verify_password_correct() -> None:
    """Correct password verifies successfully against its hash."""
    from backend.services.auth import hash_password, verify_password

    hashed = hash_password("mysecretpassword")
    assert verify_password("mysecretpassword", hashed) is True


def test_verify_password_wrong() -> None:
    """Wrong password fails verification."""
    from backend.services.auth import hash_password, verify_password

    hashed = hash_password("mysecretpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_returns_string() -> None:
    """Access token creation returns a non-empty string."""
    from backend.services.auth import create_access_token

    token = create_access_token(data={"sub": "testuser"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_custom_expiry() -> None:
    """Access token with custom expiry is still a valid token string."""
    from backend.services.auth import create_access_token

    token = create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(minutes=5),
    )
    assert isinstance(token, str)


def test_decode_access_token_valid() -> None:
    """A freshly created token decodes back to its subject."""
    from backend.services.auth import create_access_token, decode_access_token

    token = create_access_token(data={"sub": "testuser"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "testuser"


def test_decode_access_token_invalid() -> None:
    """An invalid token string returns None."""
    from backend.services.auth import decode_access_token

    result = decode_access_token("not.a.valid.token")
    assert result is None


def test_decode_access_token_expired() -> None:
    """An already-expired token returns None."""
    from backend.services.auth import create_access_token, decode_access_token

    token = create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(seconds=-1),
    )
    result = decode_access_token(token)
    assert result is None
