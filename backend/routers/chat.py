"""Chat and Help API router."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.app_settings import AppSettings
from backend.models.chat_log import ChatLog
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.chat import ChatConfig, ChatLogRead, ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

_AnyUserRequired = Annotated[
    User,
    Depends(
        require_role(
            UserRole.READONLY,
            UserRole.SECRETAIRE,
            UserRole.TRESORIER,
            UserRole.ADMIN,
        )
    ),
]
_AdminRequired = Annotated[User, Depends(require_role(UserRole.ADMIN))]

_SETTINGS_ID = 1
_MANUEL_PATH = Path(__file__).resolve().parents[2] / "doc" / "user" / "manuel.md"


@router.get("/chat/config", response_model=ChatConfig)
async def get_chat_config(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatConfig:
    """Return whether the chat feature is enabled (public endpoint, no auth required)."""
    result = await db.execute(
        select(AppSettings.chat_api_key).where(AppSettings.id == _SETTINGS_ID)
    )
    api_key = result.scalar_one_or_none()
    return ChatConfig(enabled=bool(api_key))


@router.post("/chat", response_class=StreamingResponse)
async def chat(
    payload: ChatRequest,
    current_user: _AnyUserRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """Stream an AI response via Server-Sent Events.

    The client should use fetch + ReadableStream (not axios) to consume SSE.
    Each event is: data: {"text": "..."} or data: [DONE]
    """
    from backend.services.chat_service import stream_chat  # noqa: PLC0415

    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    return StreamingResponse(
        stream_chat(messages, current_user, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/logs", response_model=list[ChatLogRead])
async def get_chat_logs(
    _current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user_id: int | None = Query(default=None),
) -> list[ChatLogRead]:
    """Return paginated chat audit log (admin only)."""
    query = select(ChatLog).order_by(ChatLog.asked_at.desc())
    if user_id is not None:
        query = query.where(ChatLog.user_id == user_id)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [ChatLogRead.model_validate(r) for r in rows]


@router.get("/help/manual", response_class=PlainTextResponse)
async def get_manual(
    _current_user: _AnyUserRequired,
) -> str:
    """Return the user manual as raw Markdown (authenticated users only)."""
    if not _MANUEL_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manuel utilisateur introuvable.",
        )
    return _MANUEL_PATH.read_text(encoding="utf-8")
