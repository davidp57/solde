"""App comment service — CRUD for user comments."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.app_comment import AppComment
from backend.models.user import User
from backend.schemas.app_comment import AppCommentCreate, AppCommentRead


async def create_comment(db: AsyncSession, payload: AppCommentCreate, user: User) -> AppCommentRead:
    """Create a new comment for the given user."""
    comment = AppComment(user_id=user.id, content=payload.content.strip())
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    return AppCommentRead(
        id=comment.id,
        user_id=comment.user_id,
        user_name=user.username,
        content=comment.content,
        is_resolved=comment.is_resolved,
        created_at=comment.created_at,
    )


async def list_comments(db: AsyncSession, user: User, admin: bool = False) -> list[AppCommentRead]:
    """Return comments. Admins see all; regular users see only their own."""
    stmt = select(AppComment, User).join(User, User.id == AppComment.user_id)
    if not admin:
        stmt = stmt.where(AppComment.user_id == user.id)
    stmt = stmt.order_by(AppComment.created_at.desc())
    rows = (await db.execute(stmt)).all()
    return [
        AppCommentRead(
            id=comment.id,
            user_id=comment.user_id,
            user_name=u.username,
            content=comment.content,
            is_resolved=comment.is_resolved,
            created_at=comment.created_at,
        )
        for comment, u in rows
    ]


async def toggle_resolved(db: AsyncSession, comment_id: int, value: bool) -> AppCommentRead | None:
    """Set is_resolved on a comment. Returns None if not found."""
    stmt = (
        select(AppComment, User)
        .join(User, User.id == AppComment.user_id)
        .where(AppComment.id == comment_id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    comment, u = row
    comment.is_resolved = value
    await db.flush()
    return AppCommentRead(
        id=comment.id,
        user_id=comment.user_id,
        user_name=u.username,
        content=comment.content,
        is_resolved=comment.is_resolved,
        created_at=comment.created_at,
    )


async def delete_comment(db: AsyncSession, comment_id: int) -> bool:
    """Delete a comment by id. Returns False if not found."""
    comment = await db.get(AppComment, comment_id)
    if comment is None:
        return False
    await db.delete(comment)
    await db.flush()
    return True
