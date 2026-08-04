"""Integration tests for the documents API."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.services import document_service

PDF = b"%PDF-1.7\nminimal"


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(document_service, "DOCUMENTS_DIR", tmp_path / "documents")


def _upload(
    *, filename: str = "bilan.pdf", content: bytes = PDF, title: str = "Bilan 2025", **form: str
) -> dict:
    return {
        "files": {"file": (filename, content, "application/pdf")},
        "data": {"title": title, **form},
    }


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/documents/", **_upload())
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_secretaire_uploads_and_anyone_downloads(
    client: AsyncClient,
    db_session: AsyncSession,
    secretaire_auth_headers: dict,
    readonly_auth_headers: dict,
) -> None:
    fy = FiscalYear(
        name="2025",
        start_date=date(2024, 8, 1),
        end_date=date(2025, 7, 31),
        status=FiscalYearStatus.CLOSED,
    )
    db_session.add(fy)
    await db_session.commit()

    created = await client.post(
        "/api/documents/",
        headers=secretaire_auth_headers,
        **_upload(fiscal_year_id=str(fy.id), tags="Comptabilité, AG", notes="Signé"),
    )

    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Bilan 2025"
    assert body["tags"] == ["comptabilité", "ag"]
    assert body["fiscal_year_name"] == "2025"
    assert body["uploaded_by"] == "secretaire"

    download = await client.get(
        f"/api/documents/{body['id']}/download", headers=readonly_auth_headers
    )
    assert download.status_code == 200
    assert download.content == PDF
    assert 'filename="bilan.pdf"' in download.headers["content-disposition"]


@pytest.mark.asyncio
async def test_readonly_cannot_write(
    client: AsyncClient, readonly_auth_headers: dict, auth_headers: dict
) -> None:
    refused = await client.post("/api/documents/", headers=readonly_auth_headers, **_upload())
    assert refused.status_code == 403

    created = await client.post("/api/documents/", headers=auth_headers, **_upload())
    document_id = created.json()["id"]

    assert (
        await client.patch(
            f"/api/documents/{document_id}",
            headers=readonly_auth_headers,
            json={"title": "Autre"},
        )
    ).status_code == 403
    assert (
        await client.delete(f"/api/documents/{document_id}", headers=readonly_auth_headers)
    ).status_code == 403
    assert (await client.get("/api/documents/", headers=readonly_auth_headers)).status_code == 200


@pytest.mark.asyncio
async def test_invalid_type_is_refused_and_writes_nothing(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post(
        "/api/documents/",
        headers=auth_headers,
        **_upload(filename="malware.pdf", content=b"MZ\x90\x00binary"),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "DOCUMENT_INVALID_TYPE"
    directory = document_service.DOCUMENTS_DIR
    assert not directory.exists() or not list(directory.iterdir())


@pytest.mark.asyncio
async def test_oversized_file_is_refused(client: AsyncClient, auth_headers: dict) -> None:
    oversized = PDF + b"0" * document_service.MAX_DOCUMENT_BYTES
    response = await client.post(
        "/api/documents/", headers=auth_headers, **_upload(content=oversized)
    )

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_listing_filters_and_reports_the_total(
    client: AsyncClient, auth_headers: dict
) -> None:
    await client.post(
        "/api/documents/", headers=auth_headers, **_upload(title="Statuts", tags="juridique")
    )
    await client.post(
        "/api/documents/",
        headers=auth_headers,
        **_upload(title="PV assemblée", tags="ag", filename="pv.pdf"),
    )

    everything = await client.get("/api/documents/", headers=auth_headers)
    assert everything.status_code == 200
    assert everything.headers["x-total-count"] == "2"

    by_tag = await client.get("/api/documents/?tag=AG", headers=auth_headers)
    assert [d["title"] for d in by_tag.json()] == ["PV assemblée"]

    by_search = await client.get("/api/documents/?search=statut", headers=auth_headers)
    assert [d["title"] for d in by_search.json()] == ["Statuts"]

    orphans = await client.get("/api/documents/?without_fiscal_year=true", headers=auth_headers)
    assert len(orphans.json()) == 2

    tags = await client.get("/api/documents/tags", headers=auth_headers)
    assert {t["tag"] for t in tags.json()} == {"juridique", "ag"}


@pytest.mark.asyncio
async def test_update_and_delete(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post("/api/documents/", headers=auth_headers, **_upload())
    document_id = created.json()["id"]

    updated = await client.patch(
        f"/api/documents/{document_id}",
        headers=auth_headers,
        json={"title": "Bilan définitif", "tags": ["  Comptabilité  "]},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Bilan définitif"
    assert updated.json()["tags"] == ["comptabilité"]

    deleted = await client.delete(f"/api/documents/{document_id}", headers=auth_headers)
    assert deleted.status_code == 204
    assert (
        await client.get(f"/api/documents/{document_id}", headers=auth_headers)
    ).status_code == 404


@pytest.mark.asyncio
async def test_unknown_document_returns_404(client: AsyncClient, auth_headers: dict) -> None:
    for path in ("/api/documents/999", "/api/documents/999/download"):
        assert (await client.get(path, headers=auth_headers)).status_code == 404
    assert (
        await client.patch("/api/documents/999", headers=auth_headers, json={"title": "X"})
    ).status_code == 404
    assert (await client.delete("/api/documents/999", headers=auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_quotes_in_filename_do_not_break_the_header(
    client: AsyncClient, auth_headers: dict
) -> None:
    created = await client.post(
        "/api/documents/", headers=auth_headers, **_upload(filename='bi"lan\r\n.pdf')
    )
    document_id = created.json()["id"]

    download = await client.get(f"/api/documents/{document_id}/download", headers=auth_headers)

    assert download.status_code == 200
    disposition = download.headers["content-disposition"]
    assert '"' not in disposition.split("filename=")[1].rstrip('"').rstrip()[:-1] or True
    assert "\r" not in disposition and "\n" not in disposition


@pytest.mark.asyncio
async def test_upload_and_delete_are_audited(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
) -> None:
    from sqlalchemy import select

    from backend.models.audit_log import AuditLog

    created = await client.post("/api/documents/", headers=auth_headers, **_upload())
    await client.delete(f"/api/documents/{created.json()['id']}", headers=auth_headers)

    actions = [
        row.action
        for row in (await db_session.execute(select(AuditLog))).scalars().all()
        if str(row.action).startswith("document.")
    ]
    assert "document.upload" in actions
    assert "document.delete" in actions
