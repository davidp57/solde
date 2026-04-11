"""Integration tests for Excel import API."""

import io

import pytest
from httpx import AsyncClient
from sqlalchemy import select

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
    assert ws is not None
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_multi_sheet_xlsx(sheets: dict[str, tuple[list[str], list[list]]]) -> bytes:
    """Create an in-memory xlsx containing multiple sheets."""
    wb = openpyxl.Workbook()
    default_ws = wb.active
    assert default_ws is not None
    default_ws.title = next(iter(sheets))

    for index, (sheet_name, (headers, rows)) in enumerate(sheets.items()):
        ws = default_ws if index == 0 else wb.create_sheet(title=sheet_name)
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


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_gestion_reports_auxiliary_sheets(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview should distinguish recognized sheets from ignored helper sheets."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                [
                    "Date facture",
                    "Réf facture",
                    "Client",
                    "Montant",
                ],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
            ),
            "Aide - Factures": (
                [
                    "Date",
                    "Numéro",
                    "Nom",
                    "Montant",
                    "N° compte",
                    "Débit",
                    "Crédit",
                ],
                [["2025-08-01", "AIDE-001", "Aide", 55, 411100, 55, None]],
            ),
            "TODO": (
                ["Date", "Factures", "Banque", "Paiements"],
                [["2025-08-31", "DONE", "DONE", "DONE"]],
            ),
        }
    )

    response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["can_import"] is True
    assert "warnings" in data

    sheets = {sheet["name"]: sheet for sheet in data["sheets"]}
    assert sheets["Factures"]["status"] == "recognized"
    assert sheets["Factures"]["kind"] == "invoices"
    assert sheets["Factures"]["rows"] == 1
    assert sheets["Aide - Factures"]["status"] == "ignored"
    assert sheets["TODO"]["status"] == "ignored"
    assert any("Aide - Factures" in warning for warning in data["warnings"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_gestion_estimates_contacts_from_invoices_and_payments(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview should estimate candidate contacts from invoice and payment sheets."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [
                    ["2025-08-01", "2025-0142", "Christine LOPES", 55],
                    ["2025-08-02", "2025-0143", "Thi BE NGUYEN", 154],
                ],
            ),
            "Paiements": (
                ["Réf facture", "Adhérent", "Montant", "Date paiement"],
                [
                    ["2025-0142", "Christine LOPES", 55, "2025-08-02"],
                    ["2025-0144", "Franck LEVY", 208, "2025-08-03"],
                ],
            ),
        }
    )

    response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["estimated_invoices"] == 2
    assert data["estimated_payments"] == 2
    assert data["estimated_contacts"] == 3


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_accept_contacts_sheet_without_prenom(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should accept a contacts sheet when only nom is required."""
    content = _make_multi_sheet_xlsx(
        {
            "Contacts": (
                ["Nom", "Email"],
                [
                    ["Christine LOPES", "christine@example.test"],
                    ["Thi BE NGUYEN", "thi@example.test"],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    sheets = {sheet["name"]: sheet for sheet in preview_data["sheets"]}
    assert sheets["Contacts"]["status"] == "recognized"
    assert sheets["Contacts"]["kind"] == "contacts"
    assert sheets["Contacts"]["rows"] == 2
    assert preview_data["estimated_contacts"] == 2
    assert preview_data["can_import"] is True

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["contacts_created"] == 2


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_accept_payment_matched_by_contact(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should both accept payments matched through the contact."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
            ),
            "Paiements": (
                ["Adhérent", "Montant", "Date paiement", "Mode de règlement"],
                [["Christine LOPES", 55, "2025-08-02", "Chèque"]],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["estimated_invoices"] == 1
    assert preview_data["estimated_payments"] == 1
    assert preview_data["can_import"] is True

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["invoices_created"] == 1
    assert import_data["payments_created"] == 1


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_gestion_blocks_partial_import_when_a_recognized_sheet_is_invalid(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Import should refuse the whole file when a recognized sheet is unsupported."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
            ),
            "Paiements": (
                ["Date paiement", "Montant", "Mode de règlement"],
                [["2025-08-02", 55, "Chèque"]],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any("Paiements" in error for error in preview_data["errors"])

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["invoices_created"] == 0
    assert import_data["payments_created"] == 0
    assert import_data["contacts_created"] == 0
    assert any("Paiements" in error for error in import_data["errors"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_gestion_rolls_back_all_changes_when_a_late_sheet_crashes(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Import should rollback previously flushed rows if a later sheet crashes."""
    from backend.models.contact import Contact
    from backend.models.invoice import Invoice
    from backend.services import excel_import

    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
            ),
            "Paiements": (
                ["Adhérent", "Montant", "Date paiement", "Mode de règlement"],
                [["Christine LOPES", 55, "2025-08-02", "Chèque"]],
            ),
        }
    )

    async def _crash_import_payments_sheet(db, ws, result):
        raise RuntimeError("forced late failure")

    monkeypatch.setattr(
        excel_import,
        "_import_payments_sheet",
        _crash_import_payments_sheet,
    )

    response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["contacts_created"] == 0
    assert data["invoices_created"] == 0
    assert data["payments_created"] == 0
    assert any("forced late failure" in error for error in data["errors"])

    contacts = (await db_session.execute(select(Contact))).scalars().all()
    invoices = (await db_session.execute(select(Invoice))).scalars().all()
    assert contacts == []
    assert invoices == []


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_gestion_processes_sheets_in_business_order(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Import should not depend on workbook sheet ordering for invoice-linked payments."""
    content = _make_multi_sheet_xlsx(
        {
            "Paiements": (
                ["Adhérent", "Montant", "Date paiement", "Mode de règlement"],
                [["Christine LOPES", 55, "2025-08-02", "Chèque"]],
            ),
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
            ),
        }
    )

    response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["invoices_created"] == 1
    assert data["payments_created"] == 1


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_accept_cash_sheet_with_entry_and_exit_columns(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should both process cash rows from entrée/sortie columns."""
    content = _make_multi_sheet_xlsx(
        {
            "Caisse": (
                ["Date", "Libellé", "Entrée", "Sortie"],
                [
                    ["2025-08-01", "Recette adhésion", 55, None],
                    ["2025-08-02", "Achat fournitures", None, 12],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    sheets = {sheet["name"]: sheet for sheet in preview_data["sheets"]}
    assert sheets["Caisse"]["status"] == "recognized"
    assert sheets["Caisse"]["kind"] == "cash"
    assert sheets["Caisse"]["rows"] == 2
    assert preview_data["can_import"] is True

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["cash_created"] == 2


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_accept_bank_sheet_with_debit_and_credit_columns(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should both process bank rows from débit/crédit columns."""
    content = _make_multi_sheet_xlsx(
        {
            "Banque": (
                ["Date", "Libellé", "Débit", "Crédit", "Solde"],
                [
                    ["2025-08-01", "Paiement CB", 18, None, 482],
                    ["2025-08-02", "Virement reçu", None, 55, 537],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    sheets = {sheet["name"]: sheet for sheet in preview_data["sheets"]}
    assert sheets["Banque"]["status"] == "recognized"
    assert sheets["Banque"]["kind"] == "bank"
    assert sheets["Banque"]["rows"] == 2
    assert preview_data["can_import"] is True

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["bank_created"] == 2


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_gestion_ignores_auxiliary_invoice_sheets(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Import should ignore helper invoice sheets even if they look parseable."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                [
                    "Date facture",
                    "Réf facture",
                    "Client",
                    "Montant",
                ],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
            ),
            "Aide - Factures": (
                ["Date", "Numéro", "Nom", "Montant"],
                [["2025-08-02", "2025-9999", "Feuille aide", 99]],
            ),
        }
    )

    response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["invoices_created"] == 1
    assert data["contacts_created"] == 1


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_comptabilite_ignores_report_sheets(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview should focus on journal sheets and ignore reporting sheets."""
    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [["2025-08-01", "411100", "Facture 2025-0142", 55, None]],
            ),
            "Grand Livre": (
                ["N° compte", "Intitulé", "Date", "Somme de Débit", "Somme de Crédit"],
                [["411100", "Clients", "2025-08-01", 55, 0]],
            ),
        }
    )

    response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    sheets = {sheet["name"]: sheet for sheet in data["sheets"]}
    assert sheets["Journal"]["status"] == "recognized"
    assert sheets["Journal"]["kind"] == "entries"
    assert sheets["Grand Livre"]["status"] == "ignored"
    assert any("Grand Livre" in warning for warning in data["warnings"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_comptabilite_ignores_journal_saisie(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview should not treat the helper input sheet as an importable journal."""
    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [["2025-08-01", "411100", "Facture 2025-0142", 55, None]],
            ),
            "Journal (saisie)": (
                ["379", "11152.22", "11152.22", "0", "1"],
                [["380", "999", "999", "0", "1"]],
            ),
        }
    )

    response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    sheets = {sheet["name"]: sheet for sheet in data["sheets"]}
    assert sheets["Journal"]["status"] == "recognized"
    assert sheets["Journal (saisie)"]["status"] == "ignored"
    assert any("Journal (saisie)" in warning for warning in data["warnings"])
