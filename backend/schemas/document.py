"""Pydantic schemas for the document space."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentUpdate(BaseModel):
    """Editable metadata. The stored file itself is never replaced."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    fiscal_year_id: int | None = None
    tags: list[str] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    filename: str
    mime_type: str | None
    size_bytes: int
    fiscal_year_id: int | None
    fiscal_year_name: str | None = None
    tags: list[str]
    notes: str | None
    uploaded_by: str | None
    uploaded_at: datetime.datetime


class DocumentTagRead(BaseModel):
    """A tag in use, with how many documents carry it."""

    tag: str
    count: int
