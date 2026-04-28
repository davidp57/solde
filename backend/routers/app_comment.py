"""App comments API router — POST /api/comments/, GET /api/comments/."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.app_comment import AppCommentCreate, AppCommentRead
from backend.services import app_comment_service

router = APIRouter(prefix="/comments", tags=["comments"])

_AnyUser = Annotated[User, Depends(get_current_user)]
_AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]


@router.post("/", response_model=AppCommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    payload: AppCommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _AnyUser,
) -> AppCommentRead:
    """Submit a new comment (any authenticated user)."""
    return await app_comment_service.create_comment(db, payload, current_user)


@router.get("/", response_model=list[AppCommentRead])
async def list_comments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _AnyUser,
) -> list[AppCommentRead]:
    """Return comments. Admins see all; other users see only their own."""
    is_admin = current_user.role == UserRole.ADMIN
    return await app_comment_service.list_comments(db, current_user, admin=is_admin)
