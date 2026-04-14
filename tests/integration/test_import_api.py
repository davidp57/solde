"""Integration tests for Excel import API."""

import io
import json
from datetime import date
from decimal import Decimal

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


def _make_multi_sheet_xlsx_rows(sheets: dict[str, list[list]]) -> bytes:
    """Create an in-memory xlsx containing multiple sheets with raw rows."""
    wb = openpyxl.Workbook()
    default_ws = wb.active
    assert default_ws is not None
    default_ws.title = next(iter(sheets))

    for index, (sheet_name, rows) in enumerate(sheets.items()):
        ws = default_ws if index == 0 else wb.create_sheet(title=sheet_name)
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
    assert "salaries_created" in data
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
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_test_import_shortcuts_list_and_run_configured_file(
    client: AsyncClient,
    auth_headers: dict,
    tmp_path,
) -> None:
    """Configured test shortcuts should be listed and executable."""
    from backend import config as config_module

    shortcut_file = tmp_path / "Gestion 2024.xlsx"
    shortcut_file.write_bytes(_make_simple_xlsx(["date", "montant", "nom"], [[]]))

    original_settings = config_module._settings
    config_module._settings = config_module.Settings(
        jwt_secret_key=original_settings.jwt_secret_key,
        enable_test_import_shortcuts=True,
        test_import_gestion_2024_path=str(shortcut_file),
    )
    try:
        shortcuts_response = await client.get(
            "/api/import/excel/test-shortcuts",
            headers=auth_headers,
        )

        assert shortcuts_response.status_code == 200
        shortcuts = {item["alias"]: item for item in shortcuts_response.json()}
        assert shortcuts["gestion-2024"]["available"] is True
        assert shortcuts["gestion-2024"]["file_name"] == "Gestion 2024.xlsx"
        assert shortcuts["gestion-2025"]["available"] is False

        import_response = await client.post(
            "/api/import/excel/test-shortcuts/gestion-2024",
            headers=auth_headers,
        )

        assert import_response.status_code == 200
        data = import_response.json()
        assert "contacts_created" in data
        assert data["entries_created"] == 0
    finally:
        config_module._settings = original_settings


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
    client: AsyncClient, auth_headers: dict, db_session
) -> None:
    """Preview and import should accept a contacts sheet when only nom is required."""
    from backend.models.contact import Contact

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

    contacts = list((await db_session.execute(select(Contact).order_by(Contact.nom))).scalars())
    assert [(contact.nom, contact.prenom) for contact in contacts] == [
        ("BE NGUYEN", "Thi"),
        ("LOPES", "Christine"),
    ]


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
async def test_preview_and_import_gestion_create_supplier_invoice_and_payment_from_bank_row(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Banque rows with an FF reference should create a supplier invoice and its payment."""
    from backend.models.bank import BankTransaction
    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceType
    from backend.models.payment import Payment, PaymentMethod

    content = _make_multi_sheet_xlsx(
        {
            "Banque": (
                ["Date", "Montant", "Référence", "Libellé", "Solde"],
                [
                    [
                        "2025-11-30",
                        -15,
                        "VIR INST FF-2025113019.02.03 VG53343MNDFS3S01",
                        "COJFA - 2025.10 - FF-2025113019.02.01",
                        1298.13,
                    ]
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
    assert preview_data["estimated_invoices"] == 1
    assert preview_data["estimated_payments"] == 1
    assert preview_data["estimated_contacts"] == 1
    assert sheets["Banque"]["rows"] == 1

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["bank_created"] == 1
    assert import_data["invoices_created"] == 1
    assert import_data["payments_created"] == 1

    contact = (await db_session.execute(select(Contact))).scalar_one()
    assert contact.nom == "COJFA"
    assert contact.prenom is None
    assert contact.type == ContactType.FOURNISSEUR

    invoice = (await db_session.execute(select(Invoice))).scalar_one()
    assert invoice.number == "FF-2025113019.02.01"
    assert invoice.type == InvoiceType.FOURNISSEUR
    assert invoice.reference == "FF-2025113019.02.01"
    assert invoice.description == "COJFA - 2025.10"
    assert invoice.total_amount == 15
    assert invoice.paid_amount == 15

    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.invoice_id == invoice.id
    assert payment.contact_id == contact.id
    assert payment.method == PaymentMethod.VIREMENT
    assert payment.reference == "FF-2025113019.02.01"

    bank_entry = (await db_session.execute(select(BankTransaction))).scalar_one()
    assert bank_entry.reference == "VIR INST FF-2025113019.02.03 VG53343MNDFS3S01"
    assert bank_entry.description == "COJFA - 2025.10 - FF-2025113019.02.01"


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_create_client_payment_from_bank_virement_row(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """A positive bank transfer referencing one client invoice should create a payment."""
    from backend.models.bank import BankTransaction
    from backend.models.invoice import Invoice
    from backend.models.payment import Payment, PaymentMethod

    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 55]],
            ),
            "Banque": (
                ["Date", "Montant", "Référence", "Libellé", "Solde"],
                [["2025-08-02", 55, "2025-0142", "Paiement facture client", 537]],
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
    assert import_data["bank_created"] == 1

    invoice = (await db_session.execute(select(Invoice))).scalar_one()
    payment = (await db_session.execute(select(Payment))).scalar_one()
    bank_entry = (await db_session.execute(select(BankTransaction))).scalar_one()

    assert payment.invoice_id == invoice.id
    assert payment.contact_id == invoice.contact_id
    assert payment.method == PaymentMethod.VIREMENT
    assert payment.reference == "2025-0142"
    assert payment.deposited is True
    assert payment.deposit_date == date(2025, 8, 2)
    assert bank_entry.reference == "2025-0142"
    assert bank_entry.description == "Paiement facture client"


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_create_supplier_invoice_and_payment_from_cash_row(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Caisse rows with an FF reference should create a supplier invoice and its payment."""
    from backend.models.cash import CashRegister
    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceType
    from backend.models.payment import Payment, PaymentMethod

    content = _make_multi_sheet_xlsx(
        {
            "Caisse": (
                ["Date", "Montant", "Tiers", "Commentaire", "Solde"],
                [["2025-08-04", -20, "Papeterie ABC", "FF-2025080412.00.00", 100]],
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
    assert preview_data["estimated_invoices"] == 1
    assert preview_data["estimated_payments"] == 1
    assert preview_data["estimated_contacts"] == 1
    assert sheets["Caisse"]["rows"] == 1

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["cash_created"] == 1
    assert import_data["invoices_created"] == 1
    assert import_data["payments_created"] == 1

    contact = (await db_session.execute(select(Contact))).scalar_one()
    assert contact.nom == "Papeterie ABC"
    assert contact.prenom is None
    assert contact.type == ContactType.FOURNISSEUR

    invoice = (await db_session.execute(select(Invoice))).scalar_one()
    assert invoice.number == "FF-2025080412.00.00"
    assert invoice.type == InvoiceType.FOURNISSEUR
    assert invoice.reference == "FF-2025080412.00.00"
    assert invoice.description == "Papeterie ABC"
    assert invoice.total_amount == 20
    assert invoice.paid_amount == 20

    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.invoice_id == invoice.id
    assert payment.contact_id == contact.id
    assert payment.method == PaymentMethod.ESPECES
    assert payment.reference == "FF-2025080412.00.00"

    cash_entry = (await db_session.execute(select(CashRegister))).scalar_one()
    assert cash_entry.reference == "FF-2025080412.00.00"
    assert cash_entry.contact_id == contact.id
    assert cash_entry.payment_id == payment.id
    assert cash_entry.balance_after == Decimal("-20")


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_generate_internal_transfer_entries_from_bank_rows(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Gestion import should generate internal transfer accounting entries for savings moves."""
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.services.accounting_engine import seed_default_rules

    await seed_default_rules(db_session)
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Banque": (
                ["Date", "Montant", "Référence", "Libellé", "Solde"],
                [
                    ["2025-09-06", 3000, "VIR DE LES ETUDES", "Virement interne", 5000],
                    ["2026-02-03", -2000, "VIR VERS LIVRET", "Virement interne", 3000],
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
    assert preview_response.json()["can_import"] is True

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["bank_created"] == 2
    assert import_data["entries_created"] == 4

    gestion_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry)
                .where(AccountingEntry.source_type == EntrySourceType.GESTION)
                .order_by(AccountingEntry.date, AccountingEntry.entry_number)
            )
        ).scalars()
    )

    assert {
        (entry.account_number, Decimal(str(entry.debit)), Decimal(str(entry.credit)))
        for entry in gestion_entries
    } == {
        ("512100", Decimal("3000"), Decimal("0")),
        ("512102", Decimal("0"), Decimal("3000")),
        ("512102", Decimal("2000"), Decimal("0")),
        ("512100", Decimal("0"), Decimal("2000")),
    }


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_generate_direct_bank_entries_and_deposit(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Gestion import should generate direct bank/deposit accounting coverage for known cases."""
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.models.bank import BankTransaction
    from backend.models.invoice import Invoice
    from backend.models.payment import Payment
    from backend.services.accounting_engine import seed_default_rules

    await seed_default_rules(db_session)
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 33]],
            ),
            "Paiements": (
                [
                    "Réf facture",
                    "Réf paiement",
                    "Adhérent",
                    "Montant",
                    "Date paiement",
                    "Numéro du chèque",
                    "Encaissé",
                    "Date encaissement",
                ],
                [
                    [
                        "2025-0142",
                        "Chèque",
                        "Christine LOPES",
                        33,
                        "2025-07-09",
                        "2025.08.02.01",
                        "OUI",
                        "2025-08-02",
                    ]
                ],
            ),
            "Banque": (
                ["Date", "Montant", "Référence", "Libellé", "Solde"],
                [
                    ["2025-08-02", 33, "REF05001A05", "Remise chèques", 599.76],
                    ["2025-08-11", -14.15, "SGT25050010010202", "Frais bancaires", 1069.61],
                    ["2025-08-20", -291.30, "PRLV SEPA MAIF", "Assurance MAIF - 2025", 778.31],
                    [
                        "2025-09-15",
                        -1474,
                        "TT404172509101922125314073410000511",
                        "Charges sociales (URSSAF) - 2025.07",
                        3265.82,
                    ],
                    [
                        "2025-02-18",
                        800,
                        "160570300002002025-02-141849 ACTE 131304",
                        "Subvention de la mairie (animations hiver 2025)",
                        3745.73,
                    ],
                    ["2025-12-31", 1563.47, "CM LIVRET", "INTERETS 2024 LIVRET BLEU", 5309.20],
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
    assert preview_response.json()["can_import"] is True

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["invoices_created"] == 1
    assert import_data["payments_created"] == 1
    assert import_data["bank_created"] == 6
    assert import_data["entries_created"] >= 12

    invoice = (await db_session.execute(select(Invoice))).scalar_one()
    payment = (await db_session.execute(select(Payment))).scalar_one()
    bank_rows = list(
        (
            await db_session.execute(
                select(BankTransaction).order_by(BankTransaction.date, BankTransaction.id)
            )
        ).scalars()
    )
    entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).order_by(AccountingEntry.date, AccountingEntry.entry_number)
            )
        ).scalars()
    )

    assert invoice.number == "2025-0142"
    assert payment.reference is None
    assert len(bank_rows) == 6

    gestion_entries = [entry for entry in entries if entry.source_type == EntrySourceType.GESTION]

    assert {
        (entry.account_number, Decimal(str(entry.debit)), Decimal(str(entry.credit)))
        for entry in gestion_entries
    } >= {
        ("512100", Decimal("33"), Decimal("0")),
        ("511200", Decimal("0"), Decimal("33")),
        ("627000", Decimal("14.15"), Decimal("0")),
        ("512100", Decimal("0"), Decimal("14.15")),
        ("616100", Decimal("291.30"), Decimal("0")),
        ("512100", Decimal("0"), Decimal("291.30")),
        ("431100", Decimal("1474"), Decimal("0")),
        ("512100", Decimal("0"), Decimal("1474")),
        ("512100", Decimal("800"), Decimal("0")),
        ("740000", Decimal("0"), Decimal("800")),
        ("512102", Decimal("1563.47"), Decimal("0")),
        ("768100", Decimal("0"), Decimal("1563.47")),
    }


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_import_salary_sheet(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Gestion import should create salary records and grouped salary accounting entries."""
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.models.salary import Salary

    content = _make_multi_sheet_xlsx_rows(
        {
            "Aide Salaires": [
                ["2025.07"],
                ["NOM", "Heures", "Brut", "Salariales", "Patronales", "Impôts", "Net"],
                ["LAY", 12, 1200, 150, 250, 10, 1040],
                ["WOLFF P.", 8, 800, 100, 180, 0, 700],
                ["Total", None, None, None, None, None, None],
            ]
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
    assert preview_data["estimated_salaries"] == 2
    assert sheets["Aide Salaires"]["kind"] == "salaries"
    assert sheets["Aide Salaires"]["rows"] == 2

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["contacts_created"] == 2
    assert import_data["salaries_created"] == 2
    assert import_data["entries_created"] == 9

    salaries = list(
        (await db_session.execute(select(Salary).order_by(Salary.month, Salary.id))).scalars()
    )
    assert len(salaries) == 2
    assert {salary.month for salary in salaries} == {"2025-07"}

    salary_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry)
                .where(AccountingEntry.source_type == EntrySourceType.SALARY)
                .order_by(AccountingEntry.entry_number)
            )
        ).scalars()
    )
    assert len(salary_entries) == 9
    assert {entry.group_key for entry in salary_entries} == {
        "salary-import:2025-07:accrual",
        "salary-import:2025-07:payment",
    }
    tax_entry = next((entry for entry in salary_entries if entry.account_number == "443000"), None)
    assert tax_entry is not None
    assert tax_entry.label == "Impôt sur le revenu 2025.07"
    assert tax_entry.debit == 0
    assert tax_entry.credit == 10


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_salary_groups_already_generated_from_gestion(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Salary journal groups already recreated from Gestion should be ignored on compta import."""
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    gestion_content = _make_multi_sheet_xlsx_rows(
        {
            "Aide Salaires": [
                ["2025.07"],
                ["NOM", "Heures", "Brut", "Salariales", "Patronales", "Impôts", "Net"],
                ["LAY", 12, 1200, 150, 250, 10, 1040],
                ["WOLFF", 8, 800, 100, 180, 0, 700],
            ]
        }
    )
    gestion_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", gestion_content, _XLSX_MIME)},
        headers=auth_headers,
    )
    assert gestion_response.status_code == 200
    assert gestion_response.json()["salaries_created"] == 2

    compta_content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    ["2025-07-31", "645100", "Charges patronales 2025.07", 430, None, "A"],
                    ["2025-07-31", "641000", "Salaires bruts 2025.07", 2000, None, "A"],
                    ["2025-07-31", "421000", "Salaires nets 2025.07", None, 1740, "A"],
                    ["2025-07-31", "431100", "Charges patronales 2025.07", None, 430, "A"],
                    ["2025-07-31", "431100", "Charges salariales 2025.07", None, 250, "A"],
                    ["2025-07-31", "443000", "Impôt sur le revenu 2025.07", None, 10, "A"],
                    ["2025-07-31", "421000", "Paiement salaires 2025.07", 1740, None, "B"],
                    ["2025-07-31", "512100", "Salaire LAY 2025.07", None, 1040, "B"],
                    ["2025-07-31", "512100", "Salaire WOLFF 2025.07", None, 700, "B"],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2025.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["estimated_entries"] == 0

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 9

    manual_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
            )
        ).scalars()
    )
    assert not manual_entries


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_salary_groups_with_float_rounding_noise(
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Salary groups should still be ignored when Excel numbers carry float noise."""
    gestion_content = _make_multi_sheet_xlsx_rows(
        {
            "Aide Salaires": [
                ["2024.08"],
                ["NOM", "Heures", "Brut", "Salariales", "Patronales", "Impôts", "Net"],
                ["LAY", 12, 1605, 355.36, 370.86, 0, 1249.64],
            ]
        }
    )
    gestion_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2024.xlsx", gestion_content, _XLSX_MIME)},
        headers=auth_headers,
    )
    assert gestion_response.status_code == 200

    compta_content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    [
                        "2024-09-07",
                        "645100",
                        "Charges patronales 2024.08",
                        370.86000000000005,
                        None,
                        "A",
                    ],
                    ["2024-09-07", "641000", "Salaires bruts 2024.08", 1605, None, "A"],
                    [
                        "2024-09-07",
                        "421000",
                        "Salaires nets 2024.08",
                        None,
                        1249.6399999999999,
                        "A",
                    ],
                    [
                        "2024-09-07",
                        "431100",
                        "Charges patronales 2024.08",
                        None,
                        370.86000000000005,
                        "A",
                    ],
                    ["2024-09-07", "431100", "Charges salariales 2024.08", None, 355.36, "A"],
                    [
                        "2024-09-07",
                        "421000",
                        "Paiement salaires 2024.08",
                        1249.6399999999999,
                        None,
                        "B",
                    ],
                    ["2024-09-07", "512100", "Salaire LAY 2024.08", None, 1249.6399999999999, "B"],
                ],
            )
        }
    )

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2024.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 7


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_standalone_salary_tax_line_from_gestion_month(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """A standalone IR/PAS line should be ignored when Gestion already recreated that month."""
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    gestion_content = _make_multi_sheet_xlsx_rows(
        {
            "Aide Salaires": [
                ["2024.11"],
                ["NOM", "Heures", "Brut", "Salariales", "Patronales", "Impôts", "Net"],
                ["LAY", 12, 1804.99, 398.85, 439.33, 1.3, 1404.84],
            ]
        }
    )
    gestion_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2024.xlsx", gestion_content, _XLSX_MIME)},
        headers=auth_headers,
    )
    assert gestion_response.status_code == 200

    compta_content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [["2024-12-01", "431100", "Impôt sur le revenu 2024.11", None, 1.3, "C"]],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2024.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    assert preview_response.json()["estimated_entries"] == 0

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2024.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 1

    manual_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
            )
        ).scalars()
    )
    assert not manual_entries


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_salary_groups_with_variants(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Salary-like accrual and payment groups should be ignored.

    This still applies when the imported journal uses variant splits.
    """
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    gestion_content = _make_multi_sheet_xlsx_rows(
        {
            "Aide Salaires": [
                ["2024.12"],
                ["NOM", "Heures", "Brut", "Salariales", "Patronales", "Impôts", "Net"],
                ["LAY", 12, 1200, 250, 250, 0.65, 949.35],
                ["WOLFF", 8, 504.99, 127.5, 133.84, 0, 377.49],
            ]
        }
    )
    gestion_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2024.xlsx", gestion_content, _XLSX_MIME)},
        headers=auth_headers,
    )
    assert gestion_response.status_code == 200
    assert gestion_response.json()["salaries_created"] == 2

    compta_content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    ["2024-12-31", "645100", "Charges patronales 2024.12", 391.97, None, "A"],
                    ["2024-12-31", "641000", "Salaires bruts 2024.12", 1704.99, None, "A"],
                    ["2024-12-31", "421000", "Salaires nets 2024.12", None, 1326.69, "A"],
                    ["2024-12-31", "431100", "Charges patronales 2024.12", None, 391.97, "A"],
                    ["2024-12-31", "431100", "Charges salariales 2024.12", None, 377.66, "A"],
                    ["2024-12-31", "431100", "Impôt sur le revenu 2024.12", None, 0.64, "A"],
                    ["2024-12-31", "421000", "Paiement salaires 2024.12", 1326.69, None, "B"],
                    ["2024-12-31", "512100", "Salaire LAY 2024.12", None, 1249.64, "B"],
                    ["2024-12-31", "512100", "Salaire WOLFF 2024.12", None, 77.05, "B"],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2024.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    assert preview_response.json()["estimated_entries"] == 0

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2024.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 9

    manual_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
            )
        ).scalars()
    )
    assert not manual_entries


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_partial_salary_accrual(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """A partial salary accrual group should be ignored.

    The month is already present from Gestion import.
    """
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    gestion_content = _make_multi_sheet_xlsx_rows(
        {
            "Aide Salaires": [
                ["2025.01"],
                ["NOM", "Heures", "Brut", "Salariales", "Patronales", "Impôts", "Net"],
                ["LAY", 12, 1704.99, 377.5, 383.84, 0.65, 1326.84],
            ]
        }
    )
    gestion_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", gestion_content, _XLSX_MIME)},
        headers=auth_headers,
    )
    assert gestion_response.status_code == 200
    assert gestion_response.json()["salaries_created"] == 1

    compta_content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    ["2025-02-01", "645100", "Charges patronales 2025.01", 384.64, None, "A"],
                    ["2025-02-01", "431100", "Charges patronales 2025.01", None, 384.64, "A"],
                    ["2025-02-01", "431100", "Impôt sur le revenu 2025.01", None, 0.65, "A"],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2025.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    assert preview_response.json()["estimated_entries"] == 0

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", compta_content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 3

    manual_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
            )
        ).scalars()
    )
    assert not manual_entries


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_generate_especes_deposit_from_cash_and_bank_rows(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """A bank remittance should create a deposit slip for matching cash payments."""
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.services.accounting_engine import seed_default_rules

    await seed_default_rules(db_session)
    await db_session.commit()
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [["2025-08-01", "2025-0142", "Christine LOPES", 20]],
            ),
            "Paiements": (
                [
                    "Réf facture",
                    "Réf paiement",
                    "Adhérent",
                    "Montant",
                    "Date paiement",
                    "Numéro du chèque",
                    "Encaissé",
                    "Date encaissement",
                ],
                [
                    [
                        "2025-0142",
                        "Espèces",
                        "Christine LOPES",
                        20,
                        "2025-08-01",
                        None,
                        "OUI",
                        "2025-08-02",
                    ]
                ],
            ),
            "Caisse": (
                ["Date", "Montant", "Tiers", "Commentaire", "Solde"],
                [["2025-08-02", -20, "CREDIT MUTUEL", "Remise espèces", 0]],
            ),
            "Banque": (
                ["Date", "Montant", "Référence", "Libellé", "Solde"],
                [["2025-08-02", 20, "REF-ESP-01", "Remise espèces", 520]],
            ),
        }
    )

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    gestion_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).where(
                    AccountingEntry.source_type == EntrySourceType.GESTION
                )
            )
        ).scalars()
    )

    assert {
        (entry.account_number, Decimal(str(entry.debit)), Decimal(str(entry.credit)))
        for entry in gestion_entries
    } >= {
        ("512100", Decimal("20"), Decimal("0")),
        ("531000", Decimal("0"), Decimal("20")),
    }


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
async def test_import_gestion_blocks_invoices_with_missing_or_invalid_date(
    client: AsyncClient, auth_headers: dict
) -> None:
    content = _make_multi_sheet_xlsx(
        {
            "Factures": (
                ["Date facture", "Réf facture", "Client", "Montant"],
                [
                    [None, "2025-0142", "Christine LOPES", 55],
                    ["invalid-date", "2025-0143", "Thi BE NGUYEN", 42],
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
    assert preview_data["error_details"] == [
        {
            "category": "invoice-invalid-date",
            "severity": "error",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": 2,
            "message": "date manquante ou invalide",
            "display_message": "Factures — Ligne 2 : date manquante ou invalide",
        },
        {
            "category": "invoice-invalid-date",
            "severity": "error",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": 3,
            "message": "date manquante ou invalide",
            "display_message": "Factures — Ligne 3 : date manquante ou invalide",
        },
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
    assert import_data["error_details"] == preview_data["error_details"]


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
            Contact(nom="Dupont", prenom="Alice", type=ContactType.CLIENT),
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
                "Factures — Ligne 2 : client ambigu : plusieurs contacts correspondent"
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
                "Factures — Ligne 2 : client ambigu : plusieurs contacts correspondent"
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
                "Paiements — Colonnes requises manquantes: référence facture ou contact"
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
                "Paiements — Colonnes requises manquantes: référence facture ou contact"
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
async def test_preview_and_import_gestion_block_cash_row_with_isolated_year(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Cash preview and import should block an isolated row.

    The row year is inconsistent with neighboring rows.
    """
    content = _make_multi_sheet_xlsx(
        {
            "Caisse": (
                ["Date", "Montant", "Commentaire"],
                [
                    ["2024-12-31", 30, "Cotisation"],
                    ["2024-12-31", -10, "Achat fournitures"],
                    ["2025-12-31", 40, "Don en caisse"],
                    ["2025-01-02", 15, "Cotisation"],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any("Caisse" in error and "voisines" in error for error in preview_data["errors"])
    assert preview_data["error_details"] == [
        {
            "category": "cash-suspicious-date",
            "severity": "error",
            "sheet_name": "Caisse",
            "kind": "cash",
            "row_number": 4,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Caisse — Ligne 4 : date incoherente avec les lignes voisines",
        }
    ]

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["cash_created"] == 0
    assert import_data["error_details"] == preview_data["error_details"]


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_block_cash_rows_with_clustered_dates(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Cash preview and import should block a clustered date anomaly.

    The invalid dates are surrounded by nearby valid rows.
    """
    content = _make_multi_sheet_xlsx(
        {
            "Caisse": (
                ["Date", "Montant", "Commentaire"],
                [
                    ["2026-01-02", 30, "Cotisation"],
                    ["2026-12-16", -49.14, "THIRIET ; FF-2026010218.10.41"],
                    ["2026-12-11", -300, "FNAC ; FF-2026010218.11.51"],
                    ["2026-12-17", -8.14, "CARREFOUR ; FF-2026010218.12.58"],
                    ["2026-01-05", -25, "Achat fournitures"],
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
    assert preview_data["can_import"] is False
    assert any("Caisse" in error and "voisines" in error for error in preview_data["errors"])
    assert preview_data["error_details"] == [
        {
            "category": "cash-suspicious-date",
            "severity": "error",
            "sheet_name": "Caisse",
            "kind": "cash",
            "row_number": 3,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Caisse — Ligne 3 : date incoherente avec les lignes voisines",
        },
        {
            "category": "cash-suspicious-date",
            "severity": "error",
            "sheet_name": "Caisse",
            "kind": "cash",
            "row_number": 4,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Caisse — Ligne 4 : date incoherente avec les lignes voisines",
        },
        {
            "category": "cash-suspicious-date",
            "severity": "error",
            "sheet_name": "Caisse",
            "kind": "cash",
            "row_number": 5,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Caisse — Ligne 5 : date incoherente avec les lignes voisines",
        },
    ]

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["cash_created"] == 0
    assert import_data["error_details"] == preview_data["error_details"]


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
async def test_preview_and_import_gestion_block_bank_row_with_isolated_year(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Bank preview and import should block an isolated row.

    The row year is inconsistent with neighboring rows.
    """
    content = _make_multi_sheet_xlsx(
        {
            "Banque": (
                ["Date", "Montant", "Référence", "Libellé", "Solde"],
                [
                    ["2024-12-31", 91, "2024-0281", "Paiement facture client", 5676.34],
                    ["2024-12-31", -660, "VIR FF-2024123113.28.00", "Sous traitance", 5016.34],
                    [
                        "2024-12-31",
                        -1249.64,
                        "VIR SALAIRE LAY 2024.12",
                        "Salaire LAY 2024.12",
                        3766.70,
                    ],
                    ["2025-12-31", 753, "REM CHQ REF05001A05", "Remise chèques", 4442.65],
                    ["2025-01-02", 26, "2024-0279", "Paiement facture client", 4468.65],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any("Banque" in error and "voisines" in error for error in preview_data["errors"])
    assert preview_data["error_details"] == [
        {
            "category": "bank-suspicious-date",
            "severity": "error",
            "sheet_name": "Banque",
            "kind": "bank",
            "row_number": 5,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Banque — Ligne 5 : date incoherente avec les lignes voisines",
        }
    ]

    bank_preview_sheet = next(
        sheet for sheet in preview_data["sheets"] if sheet["name"] == "Banque"
    )
    assert bank_preview_sheet["blocked_rows"] == 1
    assert bank_preview_sheet["error_details"][0]["category"] == "bank-suspicious-date"
    assert bank_preview_sheet["error_details"][0]["row_number"] == 5
    assert bank_preview_sheet["error_details"][0]["message"] == (
        "date incoherente avec les lignes voisines"
    )

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["bank_created"] == 0
    assert import_data["error_details"] == preview_data["error_details"]


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_preview_and_import_gestion_block_payment_row_with_isolated_year(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Payment preview and import should block an isolated row.

    The row year is inconsistent with neighboring rows.
    """
    content = _make_multi_sheet_xlsx(
        {
            "Paiements": (
                ["Réf facture", "Montant", "Date paiement", "Mode de règlement"],
                [
                    ["2024-0281", 91, "2024-12-31", "Chèque"],
                    ["2024-0282", 52, "2024-12-31", "Chèque"],
                    ["2024-0283", 44, "2025-12-31", "Chèque"],
                    ["2025-0001", 26, "2025-01-02", "Chèque"],
                ],
            )
        }
    )

    preview_response = await client.post(
        "/api/import/excel/gestion/preview",
        files={"file": ("Gestion 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["can_import"] is False
    assert any("Paiements" in error and "voisines" in error for error in preview_data["errors"])
    assert preview_data["error_details"] == [
        {
            "category": "payment-suspicious-date",
            "severity": "error",
            "sheet_name": "Paiements",
            "kind": "payments",
            "row_number": 4,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Paiements — Ligne 4 : date incoherente avec les lignes voisines",
        }
    ]

    import_response = await client.post(
        "/api/import/excel/gestion",
        files={"file": ("Gestion 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["payments_created"] == 0
    assert import_data["error_details"] == preview_data["error_details"]


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
async def test_preview_and_import_comptabilite_block_journal_rows_with_clustered_dates(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Comptabilite journal preview/import should block clustered dates.

    The affected run is inconsistent with surrounding rows.
    """
    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit"],
                [
                    ["2025-12-31", "512100", "2025-0255 Marie-Claire RIBEIRO", 78, None],
                    ["2025-12-31", "411100", "2025-0255 Marie-Claire RIBEIRO", None, 78],
                    ["2026-12-03", "511200", "2025-0222 Christine LOPES", 33, None],
                    ["2026-12-03", "411100", "2025-0222 Christine LOPES", None, 33],
                    ["2026-12-02", "511200", "2025-0229 Zeina NOHRA", 78, None],
                    ["2026-12-02", "411100", "2025-0229 Zeina NOHRA", None, 78],
                    ["2026-12-05", "511200", "2025-0236 Franck LEVY", 208, None],
                    ["2026-12-05", "411100", "2025-0236 Franck LEVY", None, 208],
                    ["2026-01-02", "531000", "2025-0226 Moulay HACHIMI", 104, None],
                    ["2026-01-02", "411100", "2025-0226 Moulay HACHIMI", None, 104],
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
    assert preview_data["can_import"] is False
    assert any("Journal" in error and "voisines" in error for error in preview_data["errors"])
    assert preview_data["error_details"] == [
        {
            "category": "entry-suspicious-date",
            "severity": "error",
            "sheet_name": "Journal",
            "kind": "entries",
            "row_number": 4,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Journal — Ligne 4 : date incoherente avec les lignes voisines",
        },
        {
            "category": "entry-suspicious-date",
            "severity": "error",
            "sheet_name": "Journal",
            "kind": "entries",
            "row_number": 5,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Journal — Ligne 5 : date incoherente avec les lignes voisines",
        },
        {
            "category": "entry-suspicious-date",
            "severity": "error",
            "sheet_name": "Journal",
            "kind": "entries",
            "row_number": 6,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Journal — Ligne 6 : date incoherente avec les lignes voisines",
        },
        {
            "category": "entry-suspicious-date",
            "severity": "error",
            "sheet_name": "Journal",
            "kind": "entries",
            "row_number": 7,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Journal — Ligne 7 : date incoherente avec les lignes voisines",
        },
        {
            "category": "entry-suspicious-date",
            "severity": "error",
            "sheet_name": "Journal",
            "kind": "entries",
            "row_number": 8,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Journal — Ligne 8 : date incoherente avec les lignes voisines",
        },
        {
            "category": "entry-suspicious-date",
            "severity": "error",
            "sheet_name": "Journal",
            "kind": "entries",
            "row_number": 9,
            "message": "date incoherente avec les lignes voisines",
            "display_message": "Journal — Ligne 9 : date incoherente avec les lignes voisines",
        },
    ]
    assert sheets["Journal"]["blocked_rows"] == 6

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["error_details"] == preview_data["error_details"]


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_groups_entries_using_change_num(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    ["2025-08-01", "411100", "Facture 2025-0142", 55, None, 0],
                    ["2025-08-01", "706110", "Facture 2025-0142", None, 55, 0],
                    ["2025-08-02", "512000", "Reglement", 55, None, 1],
                    ["2025-08-02", "411100", "Reglement", None, 55, 1],
                ],
            ),
        }
    )

    response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    result = await db_session.execute(
        select(AccountingEntry)
        .where(AccountingEntry.source_type == EntrySourceType.MANUAL)
        .order_by(AccountingEntry.id.asc())
    )
    entries = result.scalars().all()
    assert len(entries) == 4
    assert entries[0].group_key == entries[1].group_key
    assert entries[2].group_key == entries[3].group_key
    assert entries[0].group_key != entries[2].group_key


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_splits_balanced_subgroups_inside_same_change_num(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    [
                        "2025-10-02",
                        "611100",
                        "Sous traitance des cours - LEXIO SAS - 2025.08 ; FF-2025100212.09.02",
                        120,
                        None,
                        1,
                    ],
                    [
                        "2025-10-02",
                        "512100",
                        "Sous traitance des cours - LEXIO SAS - 2025.08 ; FF-2025100212.09.02",
                        None,
                        120,
                        1,
                    ],
                    ["2025-10-02", "645100", "Charges patronales 2025.09", 333.63, None, 1],
                    ["2025-10-02", "641000", "Salaires bruts 2025.09", 1605, None, 1],
                    ["2025-10-02", "421000", "Salaires nets 2025.09", None, 1249.64, 1],
                    ["2025-10-02", "431100", "Charges patronales 2025.09", None, 333.63, 1],
                    ["2025-10-02", "431100", "Charges salariales 2025.09", None, 355.36, 1],
                ],
            ),
        }
    )

    response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert response.status_code == 200
    result = await db_session.execute(
        select(AccountingEntry)
        .where(AccountingEntry.source_type == EntrySourceType.MANUAL)
        .order_by(AccountingEntry.id.asc())
    )
    entries = result.scalars().all()
    assert len(entries) == 7
    assert entries[0].group_key == entries[1].group_key
    assert entries[2].group_key == entries[3].group_key
    assert entries[3].group_key == entries[4].group_key
    assert entries[4].group_key == entries[5].group_key
    assert entries[5].group_key == entries[6].group_key
    assert entries[0].group_key != entries[2].group_key


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_generated_group_even_when_label_differs(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="000001",
                date=date(2025, 7, 21),
                account_number="411100",
                label="Fact. 2025-0141 32",
                debit=Decimal("170.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=257,
                group_key="invoice:257",
            ),
            AccountingEntry(
                entry_number="000002",
                date=date(2025, 7, 21),
                account_number="706110",
                label="Fact. 2025-0141 32",
                debit=Decimal("0.00"),
                credit=Decimal("170.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=257,
                group_key="invoice:257",
            ),
        ]
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    ["2025-07-21", "411100", "2025-0141 Marie-Claire RIBEIRO", 170, None, 0],
                    ["2025-07-21", "706110", "2025-0141 Marie-Claire RIBEIRO", None, 170, 0],
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
    assert preview_data["estimated_entries"] == 0
    assert preview_data["sheets"][0]["ignored_rows"] == 2

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 2
    result = await db_session.execute(
        select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
    )
    assert result.scalars().all() == []


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_client_invoice_groups_when_split(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Client invoice journal rows should be ignored.

    This remains true when an existing invoice is split differently.
    """
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceLabel, InvoiceStatus, InvoiceType

    contact = Contact(nom="ELEZI", prenom="Aleksander", type=ContactType.CLIENT)
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="2024-0192",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 8, 30),
        total_amount=Decimal("100.00"),
        paid_amount=Decimal("100.00"),
        status=InvoiceStatus.PAID,
        label=InvoiceLabel.CS,
    )
    db_session.add(invoice)
    await db_session.flush()

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 8, 30),
                account_number="411100",
                label="Fact. 2024-0192 15",
                debit=Decimal("100.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=invoice.id,
                group_key=f"invoice:{invoice.id}",
            ),
            AccountingEntry(
                entry_number="000002",
                date=date(2024, 8, 30),
                account_number="706110",
                label="Fact. 2024-0192 15",
                debit=Decimal("0.00"),
                credit=Decimal("100.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=invoice.id,
                group_key=f"invoice:{invoice.id}",
            ),
        ]
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    ["2024-08-30", "411100", "2024-0192 Aleksander ELEZI", 50, None, 15],
                    ["2024-08-30", "706110", "2024-0192 Aleksander ELEZI", None, 50, 15],
                    ["2024-08-30", "411100", "2024-0192 Aleksander ELEZI", 50, None, 16],
                    ["2024-08-30", "756000", "2024-0192 Aleksander ELEZI", None, 50, 16],
                ],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    sheets = {sheet["name"]: sheet for sheet in preview_data["sheets"]}
    assert preview_data["estimated_entries"] == 0
    assert sheets["Journal"]["ignored_rows"] == 4
    assert sheets["Journal"]["blocked_rows"] == 0

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 4
    result = await db_session.execute(
        select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
    )
    assert result.scalars().all() == []


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_client_payment_group_when_date_differs(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Client payment rows should be ignored when an equivalent payment already exists."""
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceLabel, InvoiceStatus, InvoiceType
    from backend.models.payment import Payment, PaymentMethod

    contact = Contact(nom="NOHRA", prenom="Zeina", type=ContactType.CLIENT)
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="2025-0229",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2025, 11, 29),
        total_amount=Decimal("78.00"),
        paid_amount=Decimal("78.00"),
        status=InvoiceStatus.PAID,
        label=InvoiceLabel.CS,
        description="2025-0229 Zeina NOHRA",
    )
    db_session.add(invoice)
    await db_session.flush()

    payment = Payment(
        invoice_id=invoice.id,
        contact_id=contact.id,
        date=date(2025, 12, 2),
        amount=Decimal("78.00"),
        method=PaymentMethod.CHEQUE,
        reference="2025-0229",
        notes="Cheque 2026.01.02.02",
        deposited=True,
        deposit_date=date(2025, 12, 3),
    )
    db_session.add(payment)
    await db_session.flush()

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="000001",
                date=date(2025, 11, 29),
                account_number="411100",
                label="Fact. 2025-0229 Zeina NOHRA",
                debit=Decimal("78.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=invoice.id,
                group_key=f"invoice:{invoice.id}",
            ),
            AccountingEntry(
                entry_number="000002",
                date=date(2025, 11, 29),
                account_number="706000",
                label="Fact. 2025-0229 Zeina NOHRA",
                debit=Decimal("0.00"),
                credit=Decimal("78.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=invoice.id,
                group_key=f"invoice:{invoice.id}",
            ),
            AccountingEntry(
                entry_number="000003",
                date=date(2025, 12, 2),
                account_number="511200",
                label="Règt. Chèque 2026.01.02.02",
                debit=Decimal("78.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.PAYMENT,
                source_id=payment.id,
                group_key=f"payment:{payment.id}",
            ),
            AccountingEntry(
                entry_number="000004",
                date=date(2025, 12, 2),
                account_number="411100",
                label="Règt. Chèque 2026.01.02.02",
                debit=Decimal("0.00"),
                credit=Decimal("78.00"),
                source_type=EntrySourceType.PAYMENT,
                source_id=payment.id,
                group_key=f"payment:{payment.id}",
            ),
        ]
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    ["2025-12-03", "511200", "2025-0229 Zeina NOHRA", 78, None, 18],
                    ["2025-12-03", "411100", "2025-0229 Zeina NOHRA", None, 78, 18],
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
    assert preview_data["estimated_entries"] == 0

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 2

    manual_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
            )
        ).scalars()
    )
    assert not manual_entries


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_existing_supplier_invoice_and_payment_group_by_reference(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Supplier direct-settlement rows should be ignored when invoice and payment already exist."""
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceLabel, InvoiceStatus, InvoiceType
    from backend.models.payment import Payment, PaymentMethod

    contact = Contact(nom="Théo DAUPHY", type=ContactType.FOURNISSEUR)
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="FF-2024090718.25.00",
        reference="FF-2024090718.25.00",
        type=InvoiceType.FOURNISSEUR,
        contact_id=contact.id,
        date=date(2024, 9, 7),
        total_amount=Decimal("300.00"),
        paid_amount=Decimal("300.00"),
        status=InvoiceStatus.PAID,
        label=InvoiceLabel.CS,
        description="Sous traitance des cours - Théo DAUPHY - 2024.08",
    )
    db_session.add(invoice)
    await db_session.flush()

    payment = Payment(
        invoice_id=invoice.id,
        contact_id=contact.id,
        date=date(2024, 9, 7),
        amount=Decimal("300.00"),
        method=PaymentMethod.VIREMENT,
        reference="FF-2024090718.25.00",
        notes="Sous traitance des cours - Théo DAUPHY - 2024.08",
    )
    db_session.add(payment)
    await db_session.flush()

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 9, 7),
                account_number="611100",
                label="Fact. FF-2024090718.25.00 Théo DAUPHY",
                debit=Decimal("300.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=invoice.id,
                group_key=f"invoice:{invoice.id}",
            ),
            AccountingEntry(
                entry_number="000002",
                date=date(2024, 9, 7),
                account_number="401000",
                label="Fact. FF-2024090718.25.00 Théo DAUPHY",
                debit=Decimal("0.00"),
                credit=Decimal("300.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=invoice.id,
                group_key=f"invoice:{invoice.id}",
            ),
            AccountingEntry(
                entry_number="000003",
                date=date(2024, 9, 7),
                account_number="401000",
                label="Règt. FF-2024090718.25.00",
                debit=Decimal("300.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.PAYMENT,
                source_id=payment.id,
                group_key=f"payment:{payment.id}",
            ),
            AccountingEntry(
                entry_number="000004",
                date=date(2024, 9, 7),
                account_number="512100",
                label="Règt. FF-2024090718.25.00",
                debit=Decimal("0.00"),
                credit=Decimal("300.00"),
                source_type=EntrySourceType.PAYMENT,
                source_id=payment.id,
                group_key=f"payment:{payment.id}",
            ),
        ]
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    [
                        "2024-09-07",
                        "611100",
                        "Sous traitance des cours - Théo DAUPHY - 2024.08 ; FF-2024090718.25.00",
                        300,
                        None,
                        15,
                    ],
                    [
                        "2024-09-07",
                        "512100",
                        "Sous traitance des cours - Théo DAUPHY - 2024.08 ; FF-2024090718.25.00",
                        None,
                        300,
                        15,
                    ],
                ],
            ),
        }
    )

    preview_response = await client.post(
        "/api/import/excel/comptabilite/preview",
        files={"file": ("Comptabilite 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["estimated_entries"] == 0

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2024.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    manual_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
            )
        ).scalars()
    )
    assert not manual_entries


@pytest.mark.asyncio
@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
async def test_import_comptabilite_ignores_supplier_and_salary_subgroups_same_change_num(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceLabel, InvoiceStatus, InvoiceType
    from backend.models.payment import Payment, PaymentMethod
    from backend.models.salary import Salary

    supplier = Contact(nom="LEXIO SAS", type=ContactType.FOURNISSEUR)
    employee = Contact(nom="Martin", prenom="Alice", type=ContactType.FOURNISSEUR)
    db_session.add_all([supplier, employee])
    await db_session.flush()

    invoice = Invoice(
        number="FF-2025100212.09.02",
        reference="FF-2025100212.09.02",
        type=InvoiceType.FOURNISSEUR,
        contact_id=supplier.id,
        date=date(2025, 10, 2),
        total_amount=Decimal("120.00"),
        paid_amount=Decimal("120.00"),
        status=InvoiceStatus.PAID,
        label=InvoiceLabel.CS,
        description="Sous traitance des cours - LEXIO SAS - 2025.08",
    )
    db_session.add(invoice)
    await db_session.flush()

    payment = Payment(
        invoice_id=invoice.id,
        contact_id=supplier.id,
        date=date(2025, 10, 2),
        amount=Decimal("120.00"),
        method=PaymentMethod.VIREMENT,
        reference="FF-2025100212.09.02",
        notes="Sous traitance des cours - LEXIO SAS - 2025.08",
    )
    salary = Salary(
        employee_id=employee.id,
        month="2025-09",
        hours=Decimal("35.00"),
        gross=Decimal("1605.00"),
        employee_charges=Decimal("355.36"),
        employer_charges=Decimal("333.63"),
        tax=Decimal("0.00"),
        net_pay=Decimal("1249.64"),
    )
    db_session.add_all([payment, salary])
    await db_session.flush()

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="000001",
                date=date(2025, 10, 2),
                account_number="611100",
                label="Fact. FF-2025100212.09.02 LEXIO SAS",
                debit=Decimal("120.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=invoice.id,
                group_key=f"invoice:{invoice.id}",
            ),
            AccountingEntry(
                entry_number="000002",
                date=date(2025, 10, 2),
                account_number="401000",
                label="Fact. FF-2025100212.09.02 LEXIO SAS",
                debit=Decimal("0.00"),
                credit=Decimal("120.00"),
                source_type=EntrySourceType.INVOICE,
                source_id=invoice.id,
                group_key=f"invoice:{invoice.id}",
            ),
            AccountingEntry(
                entry_number="000003",
                date=date(2025, 10, 2),
                account_number="401000",
                label="Règt. FF-2025100212.09.02",
                debit=Decimal("120.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.PAYMENT,
                source_id=payment.id,
                group_key=f"payment:{payment.id}",
            ),
            AccountingEntry(
                entry_number="000004",
                date=date(2025, 10, 2),
                account_number="512100",
                label="Règt. FF-2025100212.09.02",
                debit=Decimal("0.00"),
                credit=Decimal("120.00"),
                source_type=EntrySourceType.PAYMENT,
                source_id=payment.id,
                group_key=f"payment:{payment.id}",
            ),
        ]
    )
    await db_session.commit()

    content = _make_multi_sheet_xlsx(
        {
            "Journal": (
                ["Date", "N° compte", "Libellé de l'écriture", "Débit", "Crédit", "ChangeNum"],
                [
                    [
                        "2025-10-02",
                        "611100",
                        "Sous traitance des cours - LEXIO SAS - 2025.08 ; FF-2025100212.09.02",
                        120,
                        None,
                        1,
                    ],
                    [
                        "2025-10-02",
                        "512100",
                        "Sous traitance des cours - LEXIO SAS - 2025.08 ; FF-2025100212.09.02",
                        None,
                        120,
                        1,
                    ],
                    ["2025-10-02", "645100", "Charges patronales 2025.09", 333.63, None, 1],
                    ["2025-10-02", "641000", "Salaires bruts 2025.09", 1605, None, 1],
                    ["2025-10-02", "421000", "Salaires nets 2025.09", None, 1249.64, 1],
                    ["2025-10-02", "431100", "Charges patronales 2025.09", None, 333.63, 1],
                    ["2025-10-02", "431100", "Charges salariales 2025.09", None, 355.36, 1],
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
    assert preview_data["estimated_entries"] == 0
    assert preview_data["sheets"][0]["ignored_rows"] == 7

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 0
    assert import_data["ignored_rows"] == 7
    manual_entries = list(
        (
            await db_session.execute(
                select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
            )
        ).scalars()
    )
    assert not manual_entries


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
async def test_preview_and_import_comptabilite_ignores_exact_duplicates_and_keeps_new_rows(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
) -> None:
    """Comptabilité import should ignore exact duplicates and keep new rows."""
    from datetime import date
    from decimal import Decimal

    from sqlalchemy import select

    from backend.models.accounting_entry import AccountingEntry, EntrySourceType
    from backend.models.fiscal_year import FiscalYear, FiscalYearStatus

    fiscal_year = FiscalYear(
        name="2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        status=FiscalYearStatus.OPEN,
    )
    db_session.add(fiscal_year)

    db_session.add(
        AccountingEntry(
            entry_number="000001",
            date=date(2025, 8, 1),
            account_number="411100",
            label="Facture 2025-0142",
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
                [
                    ["2025-08-01", "411100", "Facture 2025-0142", 55, None],
                    ["2025-08-02", "706200", "Nouvelle ecriture", None, 55],
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
    assert preview_data["can_import"] is True
    assert any("auto-generees" in warning.lower() for warning in preview_data["warnings"])
    assert preview_data["estimated_entries"] == 1
    assert preview_data["sheets"][0]["ignored_rows"] == 1
    assert any(
        "deja existante" in warning.lower() for warning in preview_data["sheets"][0]["warnings"]
    )

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite 2025.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 1
    assert import_data["ignored_rows"] == 1
    assert import_data["errors"] == []

    manual_entries = (
        (
            await db_session.execute(
                select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
            )
        )
        .scalars()
        .all()
    )
    assert len(manual_entries) == 1
    assert manual_entries[0].account_number == "706200"
    assert manual_entries[0].label == "Nouvelle ecriture"
    assert manual_entries[0].fiscal_year_id == fiscal_year.id


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
    assert all("auto-generees" not in error.lower() for error in preview_data["errors"])

    import_response = await client.post(
        "/api/import/excel/comptabilite",
        files={"file": ("Comptabilite manuel.xlsx", content, _XLSX_MIME)},
        headers=auth_headers,
    )

    assert import_response.status_code == 200
    import_data = import_response.json()
    assert import_data["entries_created"] == 1
    assert all("auto-generees" not in error.lower() for error in import_data["errors"])
