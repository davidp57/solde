"""Integration tests for Excel import API."""

import io

import pytest
from httpx import AsyncClient

try:
    import openpyxl

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _make_simple_xlsx(headers: list[str], rows: list[list]) -> bytes:
    """Create a minimal in-memory xlsx with given headers and data rows."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_import_requires_auth(client: AsyncClient) -> None:
    """Import endpoints require authentication."""
    response = await client.post("/api/import/excel/gestion")
    assert response.status_code in (401, 422)


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_gestion_empty_sheet(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Uploading an xlsx with empty valid sheet returns a result dict."""
    content = _make_simple_xlsx(["date", "montant", "nom"], [[]])
    response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "contacts_created" in data
    assert "invoices_created" in data
    assert "payments_created" in data
    assert "entries_created" in data
    assert "skipped" in data
    assert "errors" in data


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_empty_sheet(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Uploading an empty comptabilité sheet returns zero counts."""
    content = _make_simple_xlsx(["date", "compte", "libellé", "débit", "crédit"], [])
    response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["entries_created"] == 0


@pytest.mark.asyncio
async def test_import_rejects_non_excel(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Uploading a non-Excel file returns 422."""
    response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("data.csv", b"nom,montant\nDupont,100", "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 422
