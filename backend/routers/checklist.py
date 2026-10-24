"""Monthly bookkeeping checklist API router."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import api_error, unprocessable
from backend.models.checklist import ChecklistSession
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.checklist import (
    ChecklistCurrent,
    ChecklistMessageCreate,
    ChecklistMessageRead,
    ChecklistMessageUpdate,
    ChecklistSessionDetail,
    ChecklistSessionOpen,
    ChecklistSessionRead,
    ChecklistStepRead,
    ChecklistStepUpdate,
)
from backend.services import checklist_service
from backend.services.audit_service import AuditAction, record_audit
from backend.services.checklist_steps import CHECKLIST_STEPS

router = APIRouter(prefix="/checklist", tags=["checklist"])

_Access = Annotated[User, Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN))]
#: Messages are written by anyone — the team, and the accountant for a later self.
_AnyUser = Annotated[User, Depends(get_current_user)]


def _checklist_exception(exc: checklist_service.ChecklistError, code: str) -> HTTPException:
    if isinstance(exc, checklist_service.ChecklistNotFoundError):
        return api_error(status.HTTP_404_NOT_FOUND, "CHECKLIST_MESSAGE_NOT_FOUND", str(exc))
    if isinstance(exc, checklist_service.ChecklistForbiddenError):
        return api_error(status.HTTP_403_FORBIDDEN, "CHECKLIST_MESSAGE_FORBIDDEN", str(exc))
    return unprocessable(code, str(exc))


async def _build_detail(
    db: AsyncSession, session: ChecklistSession, *, with_signals: bool = True
) -> ChecklistSessionDetail:
    states = {s.step_key: s for s in await checklist_service.get_step_states(db, session.id)}
    steps = [
        ChecklistStepRead(
            key=step.key,
            block=step.block.value,
            external=step.external,
            signal=step.signal.value if step.signal else None,
            route=step.route,
            checked=bool(states[step.key].checked) if step.key in states else False,
            checked_by=states[step.key].checked_by if step.key in states else None,
            checked_at=states[step.key].checked_at if step.key in states else None,
            carried_over=bool(states[step.key].carried_over) if step.key in states else False,
        )
        for step in CHECKLIST_STEPS
    ]
    signals = (
        await checklist_service.compute_signals(db, period=session.period) if with_signals else {}
    )
    cutoff = await checklist_service.late_cutoff(db)
    messages = [
        ChecklistMessageRead.model_validate(message).model_copy(
            update={"late": checklist_service.is_message_late(message, cutoff)}
        )
        for message in await checklist_service.get_session_messages(db, session)
    ]
    return ChecklistSessionDetail(
        session=ChecklistSessionRead.model_validate(session),
        steps=steps,
        signals=signals,
        messages=messages,
    )


@router.get("/current", response_model=ChecklistCurrent)
async def get_current_checklist(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _Access,
) -> ChecklistCurrent:
    """The open session with its steps and signals, or what a new one would be about."""
    session = await checklist_service.get_open_session(db)
    detail = await _build_detail(db, session) if session is not None else None
    checked = sum(1 for s in detail.steps if s.checked) if detail else 0
    return ChecklistCurrent(
        detail=detail,
        suggested_period=await checklist_service.next_available_period(db, date.today()),
        checked_count=checked,
        total_count=len(CHECKLIST_STEPS),
        waiting_messages=await checklist_service.count_waiting_messages(db),
    )


@router.post(
    "/sessions",
    response_model=ChecklistSessionDetail,
    status_code=status.HTTP_201_CREATED,
)
async def open_checklist_session(
    payload: ChecklistSessionOpen,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _Access,
) -> ChecklistSessionDetail:
    period = payload.period or await checklist_service.next_available_period(db, date.today())
    try:
        session = await checklist_service.open_session(
            db, period=period, actor=current_user.username
        )
    except checklist_service.ChecklistError as exc:
        raise unprocessable("CHECKLIST_SESSION_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.CHECKLIST_SESSION_OPENED,
        actor=current_user,
        target_id=session.id,
        target_type="checklist_session",
        detail={"period": session.period},
    )
    return await _build_detail(db, session)


@router.get("/sessions", response_model=list[ChecklistSessionRead])
async def list_checklist_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _Access,
    limit: int = Query(default=24, ge=1, le=120),
) -> list[ChecklistSessionRead]:
    sessions = await checklist_service.list_sessions(db, limit=limit)
    return [ChecklistSessionRead.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChecklistSessionDetail)
async def get_checklist_session(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _Access,
) -> ChecklistSessionDetail:
    session = await checklist_service.get_session(db, session_id)
    if session is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "CHECKLIST_SESSION_NOT_FOUND", "not found")
    # A past session is read back for the record: its signals describe today, not
    # the day it was held, so they would be misleading.
    return await _build_detail(db, session, with_signals=False)


@router.put("/sessions/{session_id}/steps/{step_key}", response_model=ChecklistSessionDetail)
async def set_checklist_step(
    session_id: int,
    step_key: str,
    payload: ChecklistStepUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _Access,
) -> ChecklistSessionDetail:
    session = await checklist_service.get_session(db, session_id)
    if session is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "CHECKLIST_SESSION_NOT_FOUND", "not found")
    try:
        await checklist_service.set_step(
            db,
            session=session,
            step_key=step_key,
            checked=payload.checked,
            actor=current_user.username,
        )
    except checklist_service.ChecklistError as exc:
        raise unprocessable("CHECKLIST_STEP_INVALID", str(exc)) from exc
    return await _build_detail(db, session)


@router.post("/sessions/{session_id}/close", response_model=ChecklistSessionRead)
async def close_checklist_session(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _Access,
) -> ChecklistSessionRead:
    """Close a session, complete or not — what is left unchecked carries over."""
    session = await checklist_service.get_session(db, session_id)
    if session is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "CHECKLIST_SESSION_NOT_FOUND", "not found")
    try:
        closed = await checklist_service.close_session(
            db, session=session, actor=current_user.username
        )
    except checklist_service.ChecklistError as exc:
        raise unprocessable("CHECKLIST_SESSION_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.CHECKLIST_SESSION_CLOSED,
        actor=current_user,
        target_id=closed.id,
        target_type="checklist_session",
        detail={"period": closed.period},
    )
    return ChecklistSessionRead.model_validate(closed)


@router.put("/sessions/{session_id}/messages/{message_id}", response_model=ChecklistSessionDetail)
async def set_checklist_message(
    session_id: int,
    message_id: int,
    payload: ChecklistMessageUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _Access,
) -> ChecklistSessionDetail:
    session = await checklist_service.get_session(db, session_id)
    if session is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "CHECKLIST_SESSION_NOT_FOUND", "not found")
    try:
        await checklist_service.set_message(
            db,
            session=session,
            message_id=message_id,
            checked=payload.checked,
            actor=current_user.username,
        )
    except checklist_service.ChecklistError as exc:
        raise _checklist_exception(exc, "CHECKLIST_MESSAGE_INVALID") from exc
    return await _build_detail(db, session)


@router.post("/messages", response_model=ChecklistMessageRead, status_code=status.HTTP_201_CREATED)
async def add_checklist_message(
    payload: ChecklistMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _AnyUser,
) -> ChecklistMessageRead:
    """Leave a message for the accountant, read at the top of the next session."""
    try:
        message = await checklist_service.add_message(
            db, content=payload.content, author=current_user.username
        )
    except checklist_service.ChecklistError as exc:
        raise _checklist_exception(exc, "CHECKLIST_MESSAGE_INVALID") from exc
    return ChecklistMessageRead.model_validate(message)


@router.get("/messages/mine", response_model=list[ChecklistMessageRead])
async def list_my_checklist_messages(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _AnyUser,
) -> list[ChecklistMessageRead]:
    """The caller's messages not dealt with yet."""
    messages = await checklist_service.list_waiting_messages(db, author=current_user.username)
    return [ChecklistMessageRead.model_validate(m) for m in messages]


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist_message(
    message_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _AnyUser,
) -> None:
    try:
        await checklist_service.delete_message(
            db, message_id=message_id, actor=current_user.username
        )
    except checklist_service.ChecklistError as exc:
        raise _checklist_exception(exc, "CHECKLIST_MESSAGE_INVALID") from exc
