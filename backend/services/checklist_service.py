"""Monthly bookkeeping checklist — sessions, step state and observed signals."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.checklist import (
    ChecklistPeriodType,
    ChecklistSession,
    ChecklistSessionStatus,
    ChecklistStepState,
)
from backend.services.checklist_steps import (
    CHECKLIST_STEPS,
    STEP_KEYS,
    ChecklistSignal,
)

#: Day of the month from which a session is assumed to be about the current
#: month rather than the previous one. Bookkeeping is done at the end of a month
#: or at the start of the next; before mid-month, it is the previous month's.
_PERIOD_SWITCH_DAY = 15


class ChecklistError(ValueError):
    """Raised when an operation does not fit the state of the checklist."""


def suggest_period(today: date) -> str:
    """The period a session opened today is most likely about ("2026-09")."""
    if today.day >= _PERIOD_SWITCH_DAY:
        return f"{today.year:04d}-{today.month:02d}"
    previous_month = today.replace(day=1) - timedelta(days=1)
    return f"{previous_month.year:04d}-{previous_month.month:02d}"


def _period_end(period: str) -> date:
    """Last day of a period — the statement brings later rows, which are not its work."""
    year, month = (int(part) for part in period.split("-"))
    first_of_next = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return first_of_next - timedelta(days=1)


def _next_period(period: str) -> str:
    year, month = (int(part) for part in period.split("-"))
    return f"{year + 1:04d}-01" if month == 12 else f"{year:04d}-{month + 1:02d}"


async def next_available_period(db: AsyncSession, today: date) -> str:
    """The period a new session would be about, skipping the ones already held.

    Suggesting a month that was already worked on would offer the user an action
    that can only fail — the period is unique.
    """
    result = await db.execute(select(ChecklistSession.period))
    taken = set(result.scalars().all())
    period = suggest_period(today)
    while period in taken:
        period = _next_period(period)
    return period


async def get_open_session(db: AsyncSession) -> ChecklistSession | None:
    result = await db.execute(
        select(ChecklistSession).where(
            ChecklistSession.status == ChecklistSessionStatus.OPEN,
        )
    )
    return result.scalars().first()


async def get_session(db: AsyncSession, session_id: int) -> ChecklistSession | None:
    return await db.get(ChecklistSession, session_id)


async def list_sessions(db: AsyncSession, *, limit: int = 24) -> list[ChecklistSession]:
    result = await db.execute(
        select(ChecklistSession).order_by(ChecklistSession.period.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_step_states(db: AsyncSession, session_id: int) -> list[ChecklistStepState]:
    result = await db.execute(
        select(ChecklistStepState).where(ChecklistStepState.session_id == session_id)
    )
    return list(result.scalars().all())


async def _last_closed_session(db: AsyncSession) -> ChecklistSession | None:
    result = await db.execute(
        select(ChecklistSession)
        .where(ChecklistSession.status == ChecklistSessionStatus.CLOSED)
        .order_by(ChecklistSession.period.desc())
        .limit(1)
    )
    return result.scalars().first()


async def open_session(
    db: AsyncSession,
    *,
    period: str,
    actor: str | None = None,
) -> ChecklistSession:
    """Open the session for a period, carrying over what the last one left unchecked.

    Only one session may be open at a time: the question the checklist answers —
    where am I — has no answer when two are running.
    """
    existing_open = await get_open_session(db)
    if existing_open is not None:
        raise ChecklistError(f"session {existing_open.period} is still open")

    already = await db.execute(
        select(ChecklistSession).where(
            ChecklistSession.period_type == ChecklistPeriodType.MONTHLY,
            ChecklistSession.period == period,
        )
    )
    if already.scalars().first() is not None:
        raise ChecklistError(f"a session already exists for {period}")

    session = ChecklistSession(
        period_type=ChecklistPeriodType.MONTHLY,
        period=period,
        status=ChecklistSessionStatus.OPEN,
        opened_by=actor,
    )
    db.add(session)
    await db.flush()

    # Steps the previous session was closed without: they are flagged here rather
    # than listed twice, so a step appears once, in its own block, marked as late.
    previous = await _last_closed_session(db)
    if previous is not None:
        previous_states = {s.step_key: s for s in await get_step_states(db, previous.id)}
        for step in CHECKLIST_STEPS:
            state = previous_states.get(step.key)
            if state is None or not state.checked:
                db.add(
                    ChecklistStepState(
                        session_id=session.id,
                        step_key=step.key,
                        checked=False,
                        carried_over=True,
                    )
                )
        await db.flush()

    await db.refresh(session)
    return session


async def set_step(
    db: AsyncSession,
    *,
    session: ChecklistSession,
    step_key: str,
    checked: bool,
    actor: str | None = None,
) -> ChecklistStepState:
    if session.status != ChecklistSessionStatus.OPEN:
        raise ChecklistError("a closed session cannot be changed")
    if step_key not in STEP_KEYS:
        raise ChecklistError(f"unknown step '{step_key}'")

    result = await db.execute(
        select(ChecklistStepState).where(
            ChecklistStepState.session_id == session.id,
            ChecklistStepState.step_key == step_key,
        )
    )
    state = result.scalars().first()
    if state is None:
        state = ChecklistStepState(session_id=session.id, step_key=step_key)
        db.add(state)

    state.checked = checked
    state.checked_by = actor if checked else None
    state.checked_at = datetime.now() if checked else None
    await db.flush()
    await db.refresh(state)
    return state


async def close_session(
    db: AsyncSession,
    *,
    session: ChecklistSession,
    actor: str | None = None,
) -> ChecklistSession:
    """Close a session, complete or not.

    Closing an incomplete session is allowed on purpose: a step that does not
    depend on the user — a cheque nobody has handed over — must not hold the
    whole month hostage. What was left unchecked is carried over to the next one.
    """
    if session.status != ChecklistSessionStatus.OPEN:
        raise ChecklistError("session is already closed")
    session.status = ChecklistSessionStatus.CLOSED
    session.closed_at = datetime.now()
    session.closed_by = actor
    await db.flush()
    await db.refresh(session)
    return session


# ---------------------------------------------------------------------------
# Observed signals — shown next to a step, never used to tick it
# ---------------------------------------------------------------------------


async def compute_signals(db: AsyncSession, *, period: str) -> dict[str, dict[str, Any]]:
    """Facts observed for the steps that carry a signal.

    Returned as structured data, never as a sentence: the wording belongs to the
    frontend's i18n file. A step whose signal cannot be computed is simply absent
    — better nothing than an empty verdict.
    """
    from backend.models.bank import BankTransaction, BankTransactionSource  # noqa: PLC0415
    from backend.models.cash import CashCount  # noqa: PLC0415
    from backend.models.payment import Payment, PaymentMethod  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415
    from backend.services import cash_service  # noqa: PLC0415
    from backend.services import settings as settings_service  # noqa: PLC0415

    signals: dict[str, dict[str, Any]] = {}

    import_sources = (
        BankTransactionSource.IMPORT,
        BankTransactionSource.IMPORT_CSV,
        BankTransactionSource.IMPORT_OFX,
        BankTransactionSource.IMPORT_QIF,
    )
    last_import = await db.execute(
        select(
            func.max(BankTransaction.created_at),
            func.count(BankTransaction.id),
        ).where(BankTransaction.source.in_(import_sources))
    )
    imported_at, imported_count = last_import.one()
    if imported_at is not None:
        signals[ChecklistSignal.LAST_IMPORT.value] = {
            "at": imported_at.isoformat(),
            "count": imported_count,
        }

    slips = await db.execute(select(func.count(Salary.id)).where(Salary.month == period))
    signals[ChecklistSignal.SALARY_SLIPS.value] = {"count": slips.scalar_one()}

    # What is left to reconcile *for this session*, which is not the same as every
    # unreconciled row in the journal. Three natures are deliberately kept apart:
    #  - rows from an actual statement, up to the end of the period: the real work;
    #  - `manual` rows — a slip confirmed before its statement arrived — which can
    #    only be settled by a later import, so they are reported separately;
    #  - the historical carry-over (`import`, `import_excel`) and the opening
    #    balance, which were never meant to be reconciled and never will be.
    period_end = _period_end(period)
    statement_sources = (
        BankTransactionSource.IMPORT_CSV,
        BankTransactionSource.IMPORT_OFX,
        BankTransactionSource.IMPORT_QIF,
    )
    unreconciled = await db.execute(
        select(func.count(BankTransaction.id)).where(
            BankTransaction.reconciled.is_(False),
            BankTransaction.source.in_(statement_sources),
            BankTransaction.date <= period_end,
        )
    )
    awaiting = await db.execute(
        select(func.count(BankTransaction.id)).where(
            BankTransaction.reconciled.is_(False),
            BankTransaction.source == BankTransactionSource.MANUAL,
            BankTransaction.date <= period_end,
        )
    )
    signals[ChecklistSignal.UNRECONCILED.value] = {
        "count": unreconciled.scalar_one(),
        "awaiting": awaiting.scalar_one(),
    }

    last_count = await db.execute(select(func.max(CashCount.date)))
    counted_on = last_count.scalar_one()
    if counted_on is not None:
        signals[ChecklistSignal.LAST_CASH_COUNT.value] = {"date": counted_on.isoformat()}

    cash_balance = await cash_service.get_cash_balance(db)
    signals[ChecklistSignal.PENDING_CASH.value] = {"amount": str(cash_balance)}

    cheques = await db.execute(
        select(func.count(Payment.id), func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.method == PaymentMethod.CHEQUE,
            Payment.deposited.is_(False),
            Payment.in_deposit.is_(False),
        )
    )
    cheque_count, cheque_total = cheques.one()
    signals[ChecklistSignal.PENDING_CHEQUES.value] = {
        "count": cheque_count,
        "amount": str(Decimal(str(cheque_total))),
    }

    app_settings = await settings_service.get_settings(db)
    if app_settings.backup_last_run_at is not None:
        signals[ChecklistSignal.LAST_BACKUP.value] = {
            "at": app_settings.backup_last_run_at.isoformat(),
            "status": app_settings.backup_last_run_status,
        }

    return signals
