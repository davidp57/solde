"""Authentication router — login, refresh, current user and account security."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.schemas.auth import (
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
    UserAdminUpdate,
    UserCreate,
    UserPasswordReset,
    UserRead,
    UserSelfUpdate,
)
from backend.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.services.rate_limiter import login_limiter

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(_oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """FastAPI dependency returning the authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username, User.is_active))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    issued_at = payload.get("iat")
    if not isinstance(issued_at, (int, float)):
        raise credentials_exception

    password_changed_at = user.password_changed_at.replace(tzinfo=UTC).timestamp()
    if float(issued_at) < password_changed_at:
        raise credentials_exception
    return user


def require_role(*roles: UserRole) -> Callable[..., Any]:
    """Dependency factory restricting access to users with the specified roles."""

    async def _check(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check


async def _count_active_admins(db: AsyncSession) -> int:
    """Return the number of active administrator accounts."""
    count = await db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.ADMIN, User.is_active)
    )
    return int(count or 0)


def _admin_user_update_exception(
    code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> HTTPException:
    """Build a stable error payload for admin-managed user updates."""
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _account_security_exception(
    code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> HTTPException:
    """Build a stable error payload for profile and password flows."""
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


async def _acquire_admin_update_lock(db: AsyncSession) -> None:
    """Serialize admin account updates on SQLite to preserve the last-admin invariant."""
    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        await db.execute(text("BEGIN IMMEDIATE"))


async def _validate_admin_user_update(
    target_user: User,
    body: UserAdminUpdate,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Enforce admin account safety rules for role/status changes."""
    if body.role is None and body.is_active is None:
        raise _admin_user_update_exception("no_changes", "No changes requested")

    role_change = body.role is not None and body.role != target_user.role
    deactivation = body.is_active is False and target_user.is_active

    if target_user.id == current_user.id:
        if deactivation:
            raise _admin_user_update_exception(
                "self_deactivate",
                "You cannot deactivate your own account",
            )
        if role_change and body.role != UserRole.ADMIN:
            raise _admin_user_update_exception(
                "self_demote",
                "You cannot remove your own admin role",
            )

    if target_user.role == UserRole.ADMIN and target_user.is_active:
        admin_would_be_removed = deactivation or (role_change and body.role != UserRole.ADMIN)
        if admin_would_be_removed and await _count_active_admins(db) <= 1:
            raise _admin_user_update_exception(
                "last_admin",
                "At least one active admin must remain",
            )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate with username + password, return JWT tokens."""
    client_ip = request.client.host if request.client else "unknown"

    if login_limiter.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    result = await db.execute(
        select(User).where(User.username == form_data.username, User.is_active)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.password_hash):
        login_limiter.record_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    login_limiter.reset(client_ip)
    return TokenResponse(
        access_token=create_access_token(data={"sub": user.username}),
        refresh_token=create_refresh_token(user.username),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Exchange a valid refresh token for new access + refresh tokens."""
    payload = decode_access_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    username: str = payload["sub"]
    result = await db.execute(select(User).where(User.username == username, User.is_active))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return TokenResponse(
        access_token=create_access_token(data={"sub": user.username}),
        refresh_token=create_refresh_token(user.username),
    )


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return the currently authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserSelfUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Update the authenticated user's own profile fields."""
    normalized_email = body.email.strip()
    if not normalized_email:
        raise _account_security_exception("email_required", "Email is required")

    if normalized_email == current_user.email:
        raise _account_security_exception("no_changes", "No changes requested")

    existing = await db.execute(
        select(User).where(User.email == normalized_email, User.id != current_user.id)
    )
    if existing.scalar_one_or_none() is not None:
        raise _account_security_exception(
            "email_exists",
            "Email already exists",
            status.HTTP_409_CONFLICT,
        )

    current_user.email = normalized_email
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    body: PasswordChangeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Change the authenticated user's password and invalidate older tokens."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise _account_security_exception(
            "invalid_current_password",
            "Current password is incorrect",
        )
    if verify_password(body.new_password, current_user.password_hash):
        raise _account_security_exception(
            "same_password",
            "New password must differ from the current password",
        )

    current_user.password_hash = hash_password(body.new_password)
    current_user.password_changed_at = datetime.now(UTC)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def create_user(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Create a new user (admin only)."""
    existing = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get(
    "/users",
    response_model=list[UserRead],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[User]:
    """List all user accounts for admin management."""
    result = await db.execute(select(User).order_by(User.username.asc()))
    return list(result.scalars().all())


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def update_user(
    user_id: int,
    body: UserAdminUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Update a user's admin-managed fields (role, activation)."""
    await _acquire_admin_update_lock(db)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise _admin_user_update_exception(
            "user_not_found",
            "User not found",
            status.HTTP_404_NOT_FOUND,
        )

    await _validate_admin_user_update(user, body, current_user, db)

    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/users/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def reset_user_password(
    user_id: int,
    body: UserPasswordReset,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Reset a user's password through an admin-managed procedure."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise _admin_user_update_exception(
            "user_not_found",
            "User not found",
            status.HTTP_404_NOT_FOUND,
        )

    user.password_hash = hash_password(body.new_password)
    user.password_changed_at = datetime.now(UTC)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
