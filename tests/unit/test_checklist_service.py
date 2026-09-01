"""Unit tests for the monthly bookkeeping checklist service."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.checklist import ChecklistSessionStatus
from backend.services import checklist_service
from backend.services.checklist_steps import CHECKLIST_STEPS, ChecklistBlock

# ---------------------------------------------------------------------------
# Which period a session is about
# ---------------------------------------------------------------------------


def test_period_before_mid_month_is_the_previous_one() -> None:
    """Bookkeeping done on 2 October is September's."""
    assert checklist_service.suggest_period(date(2026, 10, 2)) == "2026-09"


def test_period_from_mid_month_is_the_current_one() -> None:
    assert checklist_service.suggest_period(date(2026, 9, 28)) == "2026-09"


def test_period_rolls_back_over_the_year() -> None:
    assert checklist_service.suggest_period(date(2027, 1, 3)) == "2026-12"


# ---------------------------------------------------------------------------
# The step list itself
# ---------------------------------------------------------------------------


def test_step_keys_are_unique() -> None:
    keys = [step.key for step in CHECKLIST_STEPS]
    assert len(keys) == len(set(keys))


def test_external_steps_carry_no_signal() -> None:
    """Nothing in the application can observe what happens outside it."""
    for step in CHECKLIST_STEPS:
        if step.external:
            assert step.signal is None, step.key
            assert step.route is None, step.key


def test_the_single_bank_visit_is_one_contiguous_block() -> None:
    """The whole point of the ordering: one visit to the bank's website, not two."""
    blocks = [step.block for step in CHECKLIST_STEPS]
    visit_positions = [i for i, b in enumerate(blocks) if b == ChecklistBlock.BANK_VISIT]
    assert visit_positions == list(range(visit_positions[0], visit_positions[-1] + 1))
    assert all(CHECKLIST_STEPS[i].external for i in visit_positions)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_session(db_session: AsyncSession) -> None:
    session = await checklist_service.open_session(db_session, period="2026-09", actor="zip")

    assert session.period == "2026-09"
    assert session.status == ChecklistSessionStatus.OPEN
    assert session.opened_by == "zip"


@pytest.mark.asyncio
async def test_only_one_session_open_at_a_time(db_session: AsyncSession) -> None:
    await checklist_service.open_session(db_session, period="2026-09")

    with pytest.raises(checklist_service.ChecklistError, match="still open"):
        await checklist_service.open_session(db_session, period="2026-10")


@pytest.mark.asyncio
async def test_a_period_cannot_be_opened_twice(db_session: AsyncSession) -> None:
    session = await checklist_service.open_session(db_session, period="2026-09")
    await checklist_service.close_session(db_session, session=session)

    with pytest.raises(checklist_service.ChecklistError, match="already exists"):
        await checklist_service.open_session(db_session, period="2026-09")


@pytest.mark.asyncio
async def test_check_and_uncheck_a_step(db_session: AsyncSession) -> None:
    session = await checklist_service.open_session(db_session, period="2026-09")

    state = await checklist_service.set_step(
        db_session, session=session, step_key="import_statement", checked=True, actor="zip"
    )
    assert state.checked is True
    assert state.checked_by == "zip"
    assert state.checked_at is not None

    state = await checklist_service.set_step(
        db_session, session=session, step_key="import_statement", checked=False, actor="zip"
    )
    assert state.checked is False
    assert state.checked_by is None
    assert state.checked_at is None


@pytest.mark.asyncio
async def test_unknown_step_is_refused(db_session: AsyncSession) -> None:
    session = await checklist_service.open_session(db_session, period="2026-09")

    with pytest.raises(checklist_service.ChecklistError, match="unknown step"):
        await checklist_service.set_step(
            db_session, session=session, step_key="buy_milk", checked=True
        )


@pytest.mark.asyncio
async def test_a_closed_session_cannot_be_changed(db_session: AsyncSession) -> None:
    session = await checklist_service.open_session(db_session, period="2026-09")
    await checklist_service.close_session(db_session, session=session, actor="zip")

    with pytest.raises(checklist_service.ChecklistError, match="closed session"):
        await checklist_service.set_step(
            db_session, session=session, step_key="reconcile", checked=True
        )


@pytest.mark.asyncio
async def test_closing_twice_is_refused(db_session: AsyncSession) -> None:
    session = await checklist_service.open_session(db_session, period="2026-09")
    await checklist_service.close_session(db_session, session=session)

    with pytest.raises(checklist_service.ChecklistError, match="already closed"):
        await checklist_service.close_session(db_session, session=session)


@pytest.mark.asyncio
async def test_an_incomplete_session_can_be_closed(db_session: AsyncSession) -> None:
    """A step that does not depend on the user must not hold the month hostage."""
    session = await checklist_service.open_session(db_session, period="2026-09")
    await checklist_service.set_step(
        db_session, session=session, step_key="reconcile", checked=True
    )

    closed = await checklist_service.close_session(db_session, session=session, actor="zip")

    assert closed.status == ChecklistSessionStatus.CLOSED
    assert closed.closed_by == "zip"
    assert closed.closed_at is not None


@pytest.mark.asyncio
async def test_unchecked_steps_carry_over_to_the_next_session(
    db_session: AsyncSession,
) -> None:
    first = await checklist_service.open_session(db_session, period="2026-09")
    await checklist_service.set_step(
        db_session, session=first, step_key="import_statement", checked=True
    )
    await checklist_service.close_session(db_session, session=first)

    second = await checklist_service.open_session(db_session, period="2026-10")

    states = {s.step_key: s for s in await checklist_service.get_step_states(db_session, second.id)}
    # Ticked last month: nothing to carry.
    assert "import_statement" not in states or not states["import_statement"].carried_over
    # Left unchecked: flagged as late, but not ticked.
    assert states["reconcile"].carried_over is True
    assert states["reconcile"].checked is False


@pytest.mark.asyncio
async def test_a_fully_checked_session_carries_nothing(db_session: AsyncSession) -> None:
    first = await checklist_service.open_session(db_session, period="2026-09")
    for step in CHECKLIST_STEPS:
        await checklist_service.set_step(db_session, session=first, step_key=step.key, checked=True)
    await checklist_service.close_session(db_session, session=first)

    second = await checklist_service.open_session(db_session, period="2026-10")

    states = await checklist_service.get_step_states(db_session, second.id)
    assert [s for s in states if s.carried_over] == []


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_signals_never_tick_anything(db_session: AsyncSession) -> None:
    """Signals are facts placed beside a step, never a verdict replacing the user."""
    session = await checklist_service.open_session(db_session, period="2026-09")

    signals = await checklist_service.compute_signals(db_session, period="2026-09")
    states = await checklist_service.get_step_states(db_session, session.id)

    assert signals  # something was observed
    assert all(not s.checked for s in states)


@pytest.mark.asyncio
async def test_signals_are_dated_or_counted_facts(db_session: AsyncSession) -> None:
    signals = await checklist_service.compute_signals(db_session, period="2026-09")

    # Never a bare boolean: a signal says how many, or when.
    for name, payload in signals.items():
        assert payload, name
        assert set(payload) & {"at", "date", "count", "amount"}, name


@pytest.mark.asyncio
async def test_next_period_skips_the_ones_already_held(db_session: AsyncSession) -> None:
    """Offering a month already worked on would offer an action that can only fail."""
    first = await checklist_service.open_session(db_session, period="2026-08")
    await checklist_service.close_session(db_session, session=first)

    # On 1 September, the natural suggestion is August — but it is taken.
    suggested = await checklist_service.next_available_period(db_session, date(2026, 9, 1))

    assert suggested == "2026-09"


@pytest.mark.asyncio
async def test_next_period_rolls_over_the_year(db_session: AsyncSession) -> None:
    for period in ("2026-12", "2027-01"):
        session = await checklist_service.open_session(db_session, period=period)
        await checklist_service.close_session(db_session, session=session)

    suggested = await checklist_service.next_available_period(db_session, date(2027, 1, 5))

    assert suggested == "2027-02"


@pytest.mark.asyncio
async def test_next_period_is_the_plain_suggestion_when_free(db_session: AsyncSession) -> None:
    suggested = await checklist_service.next_available_period(db_session, date(2026, 9, 20))

    assert suggested == "2026-09"
