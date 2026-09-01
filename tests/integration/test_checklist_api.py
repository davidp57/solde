"""Integration tests for the monthly bookkeeping checklist API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from backend.models.user import User


async def _open_session(client: AsyncClient, auth_headers: dict, period: str = "2026-09") -> int:
    response = await client.post(
        "/api/checklist/sessions", json={"period": period}, headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()["session"]["id"]


@pytest.mark.asyncio
async def test_current_without_any_session(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.get("/api/checklist/current", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["detail"] is None
    assert data["checked_count"] == 0
    assert data["total_count"] > 0
    # The frontend offers to start this one.
    assert len(data["suggested_period"]) == 7


@pytest.mark.asyncio
async def test_open_session_returns_the_steps_and_signals(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.post(
        "/api/checklist/sessions", json={"period": "2026-09"}, headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["session"]["period"] == "2026-09"
    assert data["session"]["status"] == "open"
    assert all(not step["checked"] for step in data["steps"])
    # External steps are flagged so the interface can set them apart.
    assert any(step["external"] for step in data["steps"])
    assert isinstance(data["signals"], dict)


@pytest.mark.asyncio
async def test_a_second_open_session_is_refused(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    await _open_session(client, auth_headers)

    response = await client.post(
        "/api/checklist/sessions", json={"period": "2026-10"}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "CHECKLIST_SESSION_INVALID"


@pytest.mark.asyncio
async def test_check_a_step(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    session_id = await _open_session(client, auth_headers)

    response = await client.put(
        f"/api/checklist/sessions/{session_id}/steps/import_statement",
        json={"checked": True},
        headers=auth_headers,
    )

    assert response.status_code == 200
    steps = {s["key"]: s for s in response.json()["steps"]}
    assert steps["import_statement"]["checked"] is True
    assert steps["import_statement"]["checked_by"] == admin_user.username
    assert steps["reconcile"]["checked"] is False


@pytest.mark.asyncio
async def test_unknown_step_is_refused(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    session_id = await _open_session(client, auth_headers)

    response = await client.put(
        f"/api/checklist/sessions/{session_id}/steps/buy_milk",
        json={"checked": True},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "CHECKLIST_STEP_INVALID"


@pytest.mark.asyncio
async def test_close_then_open_the_next_month(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    session_id = await _open_session(client, auth_headers, period="2026-09")
    await client.put(
        f"/api/checklist/sessions/{session_id}/steps/import_statement",
        json={"checked": True},
        headers=auth_headers,
    )

    close = await client.post(f"/api/checklist/sessions/{session_id}/close", headers=auth_headers)
    assert close.status_code == 200
    assert close.json()["status"] == "closed"
    assert close.json()["closed_by"] == admin_user.username

    october = await client.post(
        "/api/checklist/sessions", json={"period": "2026-10"}, headers=auth_headers
    )
    assert october.status_code == 201
    steps = {s["key"]: s for s in october.json()["steps"]}
    # Ticked in September, so nothing is late.
    assert steps["import_statement"]["carried_over"] is False
    # Left unchecked, so flagged — but not ticked.
    assert steps["reconcile"]["carried_over"] is True
    assert steps["reconcile"]["checked"] is False


@pytest.mark.asyncio
async def test_a_past_session_is_read_without_signals(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    """Signals describe today, not the day the session was held."""
    session_id = await _open_session(client, auth_headers)
    await client.post(f"/api/checklist/sessions/{session_id}/close", headers=auth_headers)

    response = await client.get(f"/api/checklist/sessions/{session_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["signals"] == {}


@pytest.mark.asyncio
async def test_history_lists_past_sessions(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    session_id = await _open_session(client, auth_headers, period="2026-09")
    await client.post(f"/api/checklist/sessions/{session_id}/close", headers=auth_headers)
    await _open_session(client, auth_headers, period="2026-10")

    response = await client.get("/api/checklist/sessions", headers=auth_headers)

    assert response.status_code == 200
    assert [s["period"] for s in response.json()] == ["2026-10", "2026-09"]


@pytest.mark.asyncio
async def test_session_not_found(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    response = await client.get("/api/checklist/sessions/9999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_an_invalid_period_is_refused(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.post(
        "/api/checklist/sessions", json={"period": "2026-13"}, headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_manager_has_no_access(
    client: AsyncClient, secretaire_user: User, secretaire_auth_headers: dict
) -> None:
    """The bookkeeping session belongs to the treasurer, like Bank and Accounting."""
    response = await client.get("/api/checklist/current", headers=secretaire_auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_treasurer_has_access(
    client: AsyncClient, tresorier_user: User, tresorier_auth_headers: dict
) -> None:
    response = await client.get("/api/checklist/current", headers=tresorier_auth_headers)
    assert response.status_code == 200
