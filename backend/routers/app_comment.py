"""App comments API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.app_comment import AppCommentCreate, AppCommentRead, AppCommentUpdate
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


@router.patch("/{comment_id}", response_model=AppCommentRead)
async def update_comment(
    comment_id: int,
    payload: AppCommentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminUser,
) -> AppCommentRead:
    """Toggle is_resolved on a comment (admin only)."""
    result = await app_comment_service.toggle_resolved(db, comment_id, payload.is_resolved)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return result


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminUser,
) -> None:
    """Delete a comment (admin only)."""
    deleted = await app_comment_service.delete_comment(db, comment_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
