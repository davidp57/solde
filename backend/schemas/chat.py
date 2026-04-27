"""Pydantic schemas for the chat and help endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Payload for POST /api/chat."""

    messages: list[ChatMessage]


class ChatConfig(BaseModel):
    """Public configuration for the chat feature."""

    enabled: bool


class ChatLogRead(BaseModel):
    """One entry from the chat audit log."""

    id: int
    user_id: int | None
    asked_at: datetime
    question: str
    prompt_tokens: int | None
    completion_tokens: int | None

    model_config = {"from_attributes": True}
