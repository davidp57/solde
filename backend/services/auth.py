"""Authentication service — password hashing and JWT token management."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from backend.config import get_settings

# JWT "type" claim: only access tokens may authenticate API requests; refresh
# tokens are only accepted by /api/auth/refresh.
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


#: bcrypt only reads this many bytes. bcrypt < 5 dropped the rest silently, and
#: the stored hashes were made that way; bcrypt 5 raises instead.
_BCRYPT_MAX_BYTES = 72


def _bcrypt_input(password: str) -> bytes:
    return password.encode()[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(_bcrypt_input(password), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    return bcrypt.checkpw(_bcrypt_input(plain_password), hashed_password.encode())


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload to encode (must include "sub" claim).
        expires_delta: Token lifetime. Defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    payload = data.copy()
    payload.setdefault("type", ACCESS_TOKEN_TYPE)
    now = datetime.now(UTC)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload["iat"] = now.timestamp()
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(username: str) -> str:
    """Create a long-lived refresh token for the given username."""
    settings = get_settings()
    return create_access_token(
        data={"sub": username, "type": REFRESH_TOKEN_TYPE},
        expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Returns:
        Decoded payload dict, or None if the token is invalid or expired.
    """
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError:
        return None
