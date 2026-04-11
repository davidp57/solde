"""Integration tests for Excel import API."""

import io
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from backend.models.import_log import ImportLog

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
async def test_import_gestion_empty_sheet(client: AsyncClient, auth_headers: dict) -> None:
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
async def test_import_comptabilite_empty_sheet(client: AsyncClient, auth_headers: dict) -> None:
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
async def test_import_rejects_non_excel(client: AsyncClient, auth_headers: dict) -> None:
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
async def test_preview_and_import_gestion_ignore_duplicate_invoice_rows_with_report(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should expose duplicate invoice rows as ignored, not blocked."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [
                    ["2025-08-01", "2025-0142", "Christine LOPES", 55],
                    ["2025-08-02", "2025-0142", "Christine LOPES", 55],
                ],
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
    sheets = {sheet["name"]: sheet for sheet in preview_data["sheets"]}
    assert preview_data["can_import"] is True
    assert preview_data["estimated_invoices"] == 1
    assert sheets["Factures"]["rows"] == 1
    assert sheets["Factures"]["ignored_rows"] == 1
    assert sheets["Factures"]["blocked_rows"] == 0
    assert any("ignoree" in warning.lower() for warning in sheets["Factures"]["warnings"])

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["invoices_created"] == 1
    assert import_data["ignored_rows"] == 1
    assert import_data["blocked_rows"] == 0
    assert any("ignoree" in warning.lower() for warning in import_data["warnings"])
    factures_sheet = next(sheet for sheet in import_data["sheets"] if sheet["name"] == "Factures")
    assert factures_sheet["imported_rows"] == 1
    assert factures_sheet["ignored_rows"] == 1
    assert factures_sheet["blocked_rows"] == 0


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_ignore_invoice_total_rows(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should ignore invoice total rows instead of blocking the file."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [
                    ["2025-08-01", "2025-0142", "Christine LOPES", 55],
                    ["Total", None, None, 55],
                ],
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
    sheets = {sheet["name"]: sheet for sheet in preview_data["sheets"]}
    assert preview_data["can_import"] is True
    assert preview_data["estimated_invoices"] == 1
    assert sheets["Factures"]["rows"] == 1
    assert sheets["Factures"]["ignored_rows"] == 1
    assert sheets["Factures"]["blocked_rows"] == 0
    assert any("total" in warning.lower() for warning in sheets["Factures"]["warnings"])

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["invoices_created"] == 1
    assert import_data["ignored_rows"] == 1
    assert import_data["blocked_rows"] == 0
    assert any("total" in warning.lower() for warning in import_data["warnings"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_ignore_existing_contact_rows_with_report(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Preview should already expose DB-existing contacts as ignored rows."""
    from backend.models.contact import Contact, ContactType

    db_session.add(Contact(nom="Christine LOPES", type=ContactType.CLIENT))
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Contacts": (
                ["Nom", "Email"],
                [["Christine LOPES", "christine@example.test"]],
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
    assert preview_data["estimated_contacts"] == 0
    assert preview_data["can_import"] is False
    assert sheets["Contacts"]["rows"] == 0
    assert sheets["Contacts"]["ignored_rows"] == 1
    assert any("deja existant" in warning.lower() for warning in sheets["Contacts"]["warnings"])

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["contacts_created"] == 0
    assert import_data["ignored_rows"] == 1
    assert any("deja existant" in warning.lower() for warning in import_data["warnings"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_ignore_existing_invoice_rows_with_report(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Preview should already expose DB-existing invoices as ignored rows."""
    from datetime import date
    from decimal import Decimal

    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceLabel, InvoiceStatus, InvoiceType

    contact = Contact(nom="Christine LOPES", type=ContactType.CLIENT)
    db_session.add(contact)
    await db_session.flush()
    db_session.add(
        Invoice(
            number="2025-0142",
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 8, 1),
            total_amount=Decimal("55"),
            paid_amount=Decimal("0"),
            status=InvoiceStatus.SENT,
            label=InvoiceLabel.CS,
        )
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
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
    sheets = {sheet["name"]: sheet for sheet in preview_data["sheets"]}
    assert preview_data["estimated_invoices"] == 0
    assert preview_data["estimated_contacts"] == 0
    assert preview_data["can_import"] is False
    assert sheets["Factures"]["rows"] == 0
    assert sheets["Factures"]["ignored_rows"] == 1
    assert any("deja existante" in warning.lower() for warning in sheets["Factures"]["warnings"])

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["invoices_created"] == 0
    assert import_data["contacts_created"] == 0
    assert import_data["ignored_rows"] == 1
    assert any("deja existante" in warning.lower() for warning in import_data["warnings"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_gestion_blocks_reimport_of_same_file_and_logs_attempts(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """A successful Gestion import should block exact reimport of the same file."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
            ),
        }
    )

    first_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert first_response.status_code == 200
    first_data = first_response.json()
    assert first_data["invoices_created"] == 1
    assert first_data["errors"] == []

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion copie.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any("deja importe" in error.lower() for error in preview_data["errors"])

    second_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion copie.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["invoices_created"] == 0
    assert any("deja importe" in error.lower() for error in second_data["errors"])

    logs = (
        (
            await db_session.execute(
                select(ImportLog).order_by(ImportLog.created_at.asc(), ImportLog.id.asc())
            )
        )
        .scalars()
        .all()
    )

    assert len(logs) == 2
    assert logs[0].import_type == "gestion"
    assert logs[0].status == "success"
    assert logs[0].file_name == "Gestion 2025.xlsx"
    assert '"invoices_created": 1' in logs[0].summary
    first_summary = json.loads(logs[0].summary or "{}")
    assert any(
        created_object.get("object_type") == "invoice"
        and created_object.get("reference") == "2025-0142"
        for created_object in first_summary.get("created_objects", [])
    )
    assert logs[1].import_type == "gestion"
    assert logs[1].status == "blocked"
    assert logs[1].file_name == "Gestion copie.xlsx"
    assert logs[0].file_hash == logs[1].file_hash


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_gestion_blocks_rows_with_missing_required_invoice_data(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should block a recognized invoice sheet with invalid rows."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [
                    ["2025-08-01", "2025-0142", "Christine LOPES", 55],
                    ["2025-08-02", "2025-0143", None, 42],
                ],
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
    assert any("Factures" in error and "Ligne 3" in error for error in preview_data["errors"])
    assert preview_data["error_details"] == [
        {
            "category": "invoice-missing-contact",
            "severity": "error",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": 3,
            "message": "client manquant",
            "display_message": "Factures — Ligne 3 : client manquant",
        }
    ]
    factures_preview_sheet = next(
        sheet for sheet in preview_data["sheets"] if sheet["name"] == "Factures"
    )
    assert factures_preview_sheet["error_details"][0]["row_number"] == 3
    assert factures_preview_sheet["error_details"][0]["message"] == "client manquant"

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["invoices_created"] == 0
    assert import_data["contacts_created"] == 0
    assert any("Factures" in error and "Ligne 3" in error for error in import_data["errors"])
    assert import_data["error_details"] == [
        {
            "category": "invoice-missing-contact",
            "severity": "error",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": 3,
            "message": "client manquant",
            "display_message": "Factures — Ligne 3 : client manquant",
        }
    ]
    factures_import_sheet = next(
        sheet for sheet in import_data["sheets"] if sheet["name"] == "Factures"
    )
    assert factures_import_sheet["error_details"][0]["row_number"] == 3


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_block_invoice_with_ambiguous_existing_contact(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Preview and import should block an invoice when several existing contacts match exactly."""
    from backend.models.contact import Contact, ContactType

    db_session.add_all(
        [
            Contact(nom="Alice", prenom="Dupont", type=ContactType.CLIENT),
            Contact(nom="Alice Dupont", prenom=None, type=ContactType.CLIENT),
        ]
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Alice Dupont", 55]],
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
    assert preview_data["estimated_invoices"] == 0
    assert any(
        "Factures" in error and "ambigu" in error.lower() for error in preview_data["errors"]
    )
    assert preview_data["error_details"] == [
        {
            "category": "invoice-ambiguous-contact",
            "severity": "error",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": 2,
            "message": "client ambigu : plusieurs contacts correspondent",
            "display_message": (
                "Factures — Ligne 2 : client ambigu : plusieurs contacts "
                "correspondent"
            ),
        }
    ]

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["invoices_created"] == 0
    assert import_data["contacts_created"] == 0
    assert any("Factures" in error and "ambigu" in error.lower() for error in import_data["errors"])
    assert import_data["error_details"] == [
        {
            "category": "invoice-ambiguous-contact",
            "severity": "error",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": 2,
            "message": "client ambigu : plusieurs contacts correspondent",
            "display_message": (
                "Factures — Ligne 2 : client ambigu : plusieurs contacts "
                "correspondent"
            ),
        }
    ]


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_block_payment_without_match(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should block payments that cannot be matched to any invoice."""
    content = _make_multi_sheet_xlsx(
        {
            "Paiements": (
                ["Adhérent", "Montant", "Date paiement", "Mode de règlement"],
                [["Contact inconnu", 55, "2025-08-02", "Chèque"]],
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
    assert any(
        "Paiements" in error and "rapprocher" in error.lower() for error in preview_data["errors"]
    )

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["payments_created"] == 0
    assert any(
        "Paiements" in error and "rapprocher" in error.lower() for error in import_data["errors"]
    )


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_accept_payment_matched_against_existing_invoice(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Preview and import should accept a payment-only file when DB data already resolves it."""
    from datetime import date
    from decimal import Decimal

    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceLabel, InvoiceStatus, InvoiceType

    contact = Contact(nom="Christine LOPES", type=ContactType.CLIENT)
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="2025-0142",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2025, 8, 1),
        total_amount=Decimal("55"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
        label=InvoiceLabel.CS,
    )
    db_session.add(invoice)
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
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
    assert preview_data["can_import"] is True
    assert preview_data["estimated_payments"] == 1

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["payments_created"] == 1


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_block_payment_with_ambiguous_invoice_reference(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Preview and import should block a payment when an invoice reference is ambiguous."""
    from datetime import date
    from decimal import Decimal

    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceLabel, InvoiceStatus, InvoiceType

    first_contact = Contact(nom="Christine LOPES", type=ContactType.CLIENT)
    second_contact = Contact(nom="Thi BE NGUYEN", type=ContactType.CLIENT)
    db_session.add_all([first_contact, second_contact])
    await db_session.flush()

    db_session.add_all(
        [
            Invoice(
                number="2025-0142",
                type=InvoiceType.CLIENT,
                contact_id=first_contact.id,
                date=date(2025, 8, 1),
                total_amount=Decimal("55"),
                paid_amount=Decimal("0"),
                status=InvoiceStatus.SENT,
                label=InvoiceLabel.CS,
            ),
            Invoice(
                number="2025-0143",
                type=InvoiceType.CLIENT,
                contact_id=second_contact.id,
                date=date(2025, 8, 2),
                total_amount=Decimal("42"),
                paid_amount=Decimal("0"),
                status=InvoiceStatus.SENT,
                label=InvoiceLabel.CS,
            ),
        ]
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Paiements": (
                ["Réf facture", "Montant", "Date paiement", "Mode de règlement"],
                [["2025-014", 55, "2025-08-02", "Chèque"]],
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
    assert any(
        "Paiements" in error and "ambigu" in error.lower() for error in preview_data["errors"]
    )

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["payments_created"] == 0
    assert any(
        "Paiements" in error and "ambigu" in error.lower() for error in import_data["errors"]
    )


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_block_payment_with_ambiguous_contact_match(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should block a contact-based payment when several invoices fit."""
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [
                    ["2025-08-01", "2025-0142", "Christine LOPES", 55],
                    ["2025-08-15", "2025-0149", "Christine LOPES", 42],
                ],
            ),
            "Paiements": (
                ["Adhérent", "Montant", "Date paiement", "Mode de règlement"],
                [["Christine LOPES", 55, "2025-08-20", "Chèque"]],
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
    assert any(
        "Paiements" in error and "ambigu" in error.lower() for error in preview_data["errors"]
    )

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["payments_created"] == 0
    assert any(
        "Paiements" in error and "ambigu" in error.lower() for error in import_data["errors"]
    )


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
    assert preview_data["error_details"] == [
        {
            "category": "payment-missing-columns",
            "severity": "error",
            "sheet_name": "Paiements",
            "kind": "payments",
            "row_number": None,
            "message": "Colonnes requises manquantes: référence facture ou contact",
            "display_message": (
                "Paiements — Colonnes requises manquantes: "
                "référence facture ou contact"
            ),
        }
    ]

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
    assert import_data["error_details"] == [
        {
            "category": "payment-missing-columns",
            "severity": "error",
            "sheet_name": "Paiements",
            "kind": "payments",
            "row_number": None,
            "message": "Colonnes requises manquantes: référence facture ou contact",
            "display_message": (
                "Paiements — Colonnes requises manquantes: "
                "référence facture ou contact"
            ),
        }
    ]


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
async def test_import_gestion_fails_when_a_sheet_flush_error_is_caught_locally(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sheet-local flush error must still fail the whole import."""
    from backend.models.contact import Contact
    from backend.models.import_log import ImportLog

    content = _make_multi_sheet_xlsx(
        {
            "Contacts": (
                ["Nom", "Prénom", "Email"],
                [["Dupont", "Alice", "alice@example.test"]],
            ),
        }
    )

    session_type = type(db_session)
    original_flush = session_type.flush
    flush_calls = 0

    async def _fail_first_flush(self, *args, **kwargs):
        nonlocal flush_calls
        flush_calls += 1
        if flush_calls == 1:
            raise RuntimeError("forced contacts flush failure")
        return await original_flush(self, *args, **kwargs)

    monkeypatch.setattr(session_type, "flush", _fail_first_flush)

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
    assert any("forced contacts flush failure" in error for error in data["errors"])

    contacts = (await db_session.execute(select(Contact))).scalars().all()
    assert contacts == []

    logs = (await db_session.execute(select(ImportLog))).scalars().all()
    assert len(logs) == 1
    assert logs[0].status == "failed"


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
async def test_preview_and_import_gestion_accept_signed_cash_amounts_and_ignore_opening_balance(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should accept signed cash amounts and ignore opening balance rows."""
    content = _make_multi_sheet_xlsx(
        {
            "Caisse": (
                ["Date", "Montant", "Commentaire"],
                [
                    ["2025-08-01", None, "Solde positif en 2025"],
                    ["2025-08-02", 55, "Recette adhésion"],
                    ["2025-08-03", -12, "Achat fournitures"],
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
    assert preview_data["can_import"] is True
    assert sheets["Caisse"]["rows"] == 2
    assert sheets["Caisse"]["ignored_rows"] == 1
    assert sheets["Caisse"]["blocked_rows"] == 0
    assert any("solde" in warning.lower() for warning in sheets["Caisse"]["warnings"])

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["cash_created"] == 2
    assert import_data["ignored_rows"] == 1
    assert import_data["blocked_rows"] == 0
    assert any("solde" in warning.lower() for warning in import_data["warnings"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_ignore_cash_pending_deposit_without_date(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Pending bank deposits without a date should be ignored as cash forecasts."""
    content = _make_multi_sheet_xlsx(
        {
            "Caisse": (
                ["Date", "Montant", "Tiers", "Commentaire"],
                [[None, -710, "CREDIT MUTUEL", "Remise espèces"]],
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
    assert preview_data["can_import"] is False
    assert preview_data["errors"] == []
    assert sheets["Caisse"]["rows"] == 0
    assert sheets["Caisse"]["ignored_rows"] == 1
    assert sheets["Caisse"]["blocked_rows"] == 0
    assert any(
        "prevision" in warning.lower() or "remise" in warning.lower()
        for warning in sheets["Caisse"]["warnings"]
    )

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["cash_created"] == 0
    assert import_data["errors"] == []
    assert import_data["ignored_rows"] == 1
    assert any(
        "prevision" in warning.lower() or "remise" in warning.lower()
        for warning in import_data["warnings"]
    )


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_keep_blocking_other_cash_rows_without_date(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Cash rows without a date must still block when they are not pending deposits."""
    content = _make_multi_sheet_xlsx(
        {
            "Caisse": (
                ["Date", "Montant", "Commentaire"],
                [[None, -25, "Achat fournitures"]],
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
    assert preview_data["can_import"] is False
    assert any("Caisse" in error and "date" in error.lower() for error in preview_data["errors"])

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["cash_created"] == 0
    assert any("Caisse" in error and "date" in error.lower() for error in import_data["errors"])


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
async def test_preview_and_import_gestion_ignore_bank_opening_descriptive_rows(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Bank preview and import should ignore descriptive opening balance rows."""
    content = _make_multi_sheet_xlsx(
        {
            "Banque": (
                ["Date", "Montant", "Libellé", "Solde"],
                [
                    ["2025-08-01", 566.76, "Solde", 566.76],
                    [None, None, "Assurance MAIF", 566.76],
                    ["2025-08-02", -18, "Paiement CB", 548.76],
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
    assert preview_data["can_import"] is True
    assert sheets["Banque"]["rows"] == 2
    assert sheets["Banque"]["ignored_rows"] == 1
    assert sheets["Banque"]["blocked_rows"] == 0
    assert any(
        "descriptive" in warning.lower() or "solde" in warning.lower()
        for warning in sheets["Banque"]["warnings"]
    )

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["bank_created"] == 2
    assert import_data["ignored_rows"] == 1
    assert import_data["blocked_rows"] == 0


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


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_comptabilite_block_row_with_missing_account(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should block a journal row with no account number."""
    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [
                    ["2025-08-01", "411100", "Facture 2025-0142", 55, None],
                    ["2025-08-02", None, "Ligne invalide", 12, None],
                ],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any("Journal" in error and "Ligne 3" in error for error in preview_data["errors"])

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert any("Journal" in error and "Ligne 3" in error for error in import_data["errors"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_comptabilite_block_row_with_invalid_amounts(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Preview and import should block a journal row when debit/credit are not usable."""
    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [
                    ["2025-08-01", "411100", "Facture 2025-0142", 55, None],
                    ["2025-08-02", "512000", "Ligne invalide", "abc", None],
                ],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any(
        "Journal" in error and "montant" in error.lower() for error in preview_data["errors"]
    )

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert any("Journal" in error and "montant" in error.lower() for error in import_data["errors"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_comptabilite_ignore_zero_amount_rows(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Zero-amount journal rows should be ignored instead of blocking the whole file."""
    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [
                    ["2025-08-01", "411100", "Facture 2025-0142", 55, None],
                    ["2025-08-02", "431100", "Impôt sur le revenu 2025.08", 0, 0],
                    ["2025-08-02", "512000", "Banque", None, 55],
                ],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    sheets = {sheet["name"]: sheet for sheet in preview_data["sheets"]}
    assert preview_data["can_import"] is True
    assert preview_data["estimated_entries"] == 2
    assert sheets["Journal"]["rows"] == 2
    assert sheets["Journal"]["ignored_rows"] == 1
    assert sheets["Journal"]["blocked_rows"] == 0
    assert any(
        "nuls" in warning.lower() or "zero" in warning.lower()
        for warning in sheets["Journal"]["warnings"]
    )

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 2
    assert import_data["ignored_rows"] == 1
    assert import_data["blocked_rows"] == 0


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_blocks_reimport_of_same_file(
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """A successful Comptabilité import should block exact reimport of the same file."""
    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [["2025-08-01", "411100", "Facture 2025-0142", 55, None]],
            ),
        }
    )

    first_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert first_response.status_code == 200
    first_data = first_response.json()
    assert first_data["entries_created"] == 1
    assert first_data["errors"] == []

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite copie.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any("deja importe" in error.lower() for error in preview_data["errors"])

    second_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite copie.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["entries_created"] == 0
    assert any("deja importe" in error.lower() for error in second_data["errors"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_comptabilite_block_when_generated_gestion_entries_exist(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Comptabilité import should be blocked if gestion-generated entries already exist."""
    from datetime import date
    from decimal import Decimal

    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    db_session.add(
        AccountingEntry(
            entry_number="000001",
            date=date(2025, 8, 1),
            account_number="411100",
            label="Facture gestion existante",
            debit=Decimal("55"),
            credit=Decimal("0"),
            source_type=EntrySourceType.INVOICE,
            source_id=1,
        )
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [["2025-08-01", "411100", "Facture 2025-0142", 55, None]],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any("auto-generees" in error.lower() for error in preview_data["errors"])

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert any("auto-generees" in error.lower() for error in import_data["errors"])


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_comptabilite_allow_existing_manual_entries(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Manual accounting entries do not block a comptabilité import."""
    from datetime import date
    from decimal import Decimal

    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    db_session.add(
        AccountingEntry(
            entry_number="000001",
            date=date(2025, 7, 31),
            account_number="512000",
            label="Ecriture manuelle existante",
            debit=Decimal("0"),
            credit=Decimal("25"),
            source_type=EntrySourceType.MANUAL,
            source_id=None,
        )
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [["2025-08-01", "411100", "Facture 2025-0142", 55, None]],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite manuel.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is True
    assert not any("auto-generees" in error.lower() for error in preview_data["errors"])

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite manuel.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 1
    assert not any("auto-generees" in error.lower() for error in import_data["errors"])
