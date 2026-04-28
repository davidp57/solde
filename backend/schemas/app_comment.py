"""Pydantic schemas for app comments."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AppCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def content_not_blank_after_strip(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be blank.")
        return v


class AppCommentUpdate(BaseModel):
    is_resolved: bool


class AppCommentRead(BaseModel):
    id: int
    user_id: int
    user_name: str
    content: str
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}
