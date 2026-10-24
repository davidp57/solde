"""Pydantic schemas for the monthly bookkeeping checklist."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.models.checklist import ChecklistPeriodType, ChecklistSessionStatus

_PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class ChecklistStepRead(BaseModel):
    """One step of the checklist, with its state in the session at hand."""

    key: str
    block: str
    external: bool
    signal: str | None
    route: str | None
    checked: bool
    checked_by: str | None
    checked_at: datetime | None
    #: Left unchecked when the previous session was closed.
    carried_over: bool


class ChecklistSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    period_type: ChecklistPeriodType
    period: str
    status: ChecklistSessionStatus
    opened_at: datetime
    opened_by: str | None
    closed_at: datetime | None
    closed_by: str | None


class ChecklistMessageRead(BaseModel):
    """A message left for the accountant."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    author: str
    created_at: datetime
    checked: bool
    checked_by: str | None
    checked_at: datetime | None
    #: Still waiting although a session was closed since it was written.
    late: bool = False


class ChecklistMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class ChecklistMessageUpdate(BaseModel):
    checked: bool


class ChecklistSessionDetail(BaseModel):
    session: ChecklistSessionRead
    steps: list[ChecklistStepRead]
    #: Observed facts keyed by signal name — shown next to a step, never ticking it.
    signals: dict[str, dict[str, Any]]
    #: Shown first, before the steps: what the team wants the accountant to know.
    messages: list[ChecklistMessageRead] = []


class ChecklistCurrent(BaseModel):
    """What the header button needs, whether or not a session is open."""

    #: None when no session is open — the frontend then offers to start one.
    detail: ChecklistSessionDetail | None
    #: The period a new session would be about, given today's date.
    suggested_period: str
    checked_count: int
    total_count: int
    #: Messages not dealt with yet, so the panel can say so before a session starts.
    waiting_messages: int = 0


class ChecklistSessionOpen(BaseModel):
    period: str | None = Field(default=None, pattern=_PERIOD_PATTERN)


class ChecklistStepUpdate(BaseModel):
    checked: bool
