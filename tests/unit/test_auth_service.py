"""Tests for authentication service (JWT + password hashing)."""

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
    assert isinstance(payload.get("iat"), (int, float))


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


def test_password_longer_than_72_bytes_is_hashed_and_verified() -> None:
    """bcrypt 5 raises past 72 bytes; the policy accepts up to 128 characters."""
    from backend.services.auth import hash_password, verify_password

    password = "Aé1" + "x" * 125  # 128 characters, 129 bytes in UTF-8
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("Aé1" + "y" * 125, hashed) is False


def test_long_password_matches_a_hash_made_by_bcrypt_4() -> None:
    """bcrypt 4 silently kept the first 72 bytes: such hashes must keep working."""
    import bcrypt

    from backend.services.auth import verify_password

    password = "B2" + "z" * 100
    legacy_hash = bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()

    assert verify_password(password, legacy_hash) is True
