"""Authentication router — login, refresh, current user."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.schemas.auth import (
    RefreshRequest,
    TokenResponse,
    UserAdminUpdate,
    UserCreate,
    UserRead,
)
from backend.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)

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


async def _validate_admin_user_update(
    target_user: User,
    body: UserAdminUpdate,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Enforce admin account safety rules for role/status changes."""
    if body.role is None and body.is_active is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes requested")

    role_change = body.role is not None and body.role != target_user.role
    deactivation = body.is_active is False and target_user.is_active

    if target_user.id == current_user.id:
        if deactivation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account",
            )
        if role_change and body.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove your own admin role",
            )

    if target_user.role == UserRole.ADMIN and target_user.is_active:
        admin_would_be_removed = deactivation or (role_change and body.role != UserRole.ADMIN)
        if admin_would_be_removed and await _count_active_admins(db) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one active admin must remain",
            )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate with username + password, return JWT tokens."""
    result = await db.execute(
        select(User).where(User.username == form_data.username, User.is_active)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await _validate_admin_user_update(user, body, current_user, db)

    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return user
