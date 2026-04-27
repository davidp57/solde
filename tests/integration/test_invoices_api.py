"""Integration tests for the invoices API."""

from datetime import date
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.services.accounting_engine import seed_default_rules


async def _create_contact(client: AsyncClient, headers: dict, nom: str = "Dupont") -> int:
    r = await client.post(
        "/api/contacts/",
        json={"type": "client", "nom": nom},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


async def _create_invoice(
    client: AsyncClient,
    headers: dict,
    contact_id: int,
    *,
    invoice_type: str = "client",
    label: str | None = None,
    lines: list | None = None,
    total_amount: float | None = None,
    invoice_date: date = date(2025, 9, 1),
) -> dict:
    payload: dict = {
        "type": invoice_type,
        "contact_id": contact_id,
        "date": str(invoice_date),
        "lines": lines or [],
    }
    if label is not None:
        payload["label"] = label
    if total_amount is not None:
        payload["total_amount"] = str(total_amount)
    r = await client.post("/api/invoices/", json=payload, headers=headers)
    assert r.status_code == 201
    return r.json()


class TestListInvoices:
    async def test_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/invoices/")
        assert r.status_code == 401

    async def test_readonly_cannot_list_invoices(
        self, client: AsyncClient, readonly_auth_headers: dict
    ):
        r = await client.get("/api/invoices/", headers=readonly_auth_headers)
        assert r.status_code == 403

    async def test_returns_empty_list(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/invoices/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    async def test_gestionnaire_can_list_invoices(
        self, client: AsyncClient, secretaire_auth_headers: dict
    ):
        r = await client.get("/api/invoices/", headers=secretaire_auth_headers)
        assert r.status_code == 200

    async def test_filter_by_type(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        await _create_invoice(client, auth_headers, cid)
        await _create_invoice(
            client, auth_headers, cid, invoice_type="fournisseur", total_amount=100.0
        )
        r = await client.get("/api/invoices/?invoice_type=client", headers=auth_headers)
        data = r.json()
        assert len(data) == 1
        assert data[0]["type"] == "client"

    async def test_filter_by_date_range(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        await _create_invoice(
            client,
            auth_headers,
            cid,
            invoice_date=date(2024, 12, 31),
        )
        kept = await _create_invoice(
            client,
            auth_headers,
            cid,
            invoice_date=date(2025, 1, 15),
        )

        r = await client.get(
            "/api/invoices/?from_date=2025-01-01&to_date=2025-12-31",
            headers=auth_headers,
        )

        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == kept["id"]


class TestCreateInvoice:
    async def test_create_client_invoice_with_lines(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        lines = [
            {
                "description": "Cours maths",
                "line_type": "cours",
                "quantity": "2",
                "unit_price": "30.00",
            },
            {
                "description": "Adhésion",
                "line_type": "adhesion",
                "quantity": "1",
                "unit_price": "20.00",
            },
        ]
        invoice = await _create_invoice(client, auth_headers, cid, lines=lines)
        assert invoice["number"] == "2025-001"
        assert float(invoice["total_amount"]) == 80.0
        assert invoice["status"] == "draft"
        assert len(invoice["lines"]) == 2
        assert invoice["label"] == "cs+a"

    async def test_create_supplier_invoice(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        invoice = await _create_invoice(
            client, auth_headers, cid, invoice_type="fournisseur", total_amount=250.0
        )
        assert invoice["number"].startswith("FF-")
        assert float(invoice["total_amount"]) == 250.0

    async def test_requires_auth(self, client: AsyncClient):
        r = await client.post(
            "/api/invoices/",
            json={"type": "client", "contact_id": 1, "date": "2025-09-01"},
        )
        assert r.status_code == 401

    async def test_invoice_number_increments(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        inv1 = await _create_invoice(client, auth_headers, cid)
        inv2 = await _create_invoice(client, auth_headers, cid)
        assert inv1["number"] == "2025-001"
        assert inv2["number"] == "2025-002"


class TestGetInvoice:
    async def test_get_existing_invoice(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(client, auth_headers, cid)
        r = await client.get(f"/api/invoices/{created['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    async def test_get_unknown_returns_404(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/invoices/99999", headers=auth_headers)
        assert r.status_code == 404


class TestUpdateInvoice:
    async def test_update_description(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(client, auth_headers, cid)
        r = await client.put(
            f"/api/invoices/{created['id']}",
            json={"description": "Updated"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["description"] == "Updated"

    async def test_update_sent_invoice_regenerates_accounting_entries(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session,
    ):
        await seed_default_rules(db_session)
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(
            client,
            auth_headers,
            cid,
            lines=[
                {
                    "description": "Cours de soutien",
                    "line_type": "cours",
                    "quantity": "1",
                    "unit_price": "130.00",
                },
                {
                    "description": "Adhesion annuelle",
                    "line_type": "adhesion",
                    "quantity": "1",
                    "unit_price": "30.00",
                },
            ],
        )
        sent_response = await client.patch(
            f"/api/invoices/{created['id']}/status",
            json={"status": "sent"},
            headers=auth_headers,
        )
        assert sent_response.status_code == 200

        initial_entries = list(
            (
                await db_session.execute(
                    select(AccountingEntry)
                    .where(AccountingEntry.source_type == EntrySourceType.INVOICE)
                    .where(AccountingEntry.source_id == created["id"])
                    .order_by(AccountingEntry.entry_number.asc())
                )
            ).scalars()
        )
        assert len(initial_entries) == 3

        update_response = await client.put(
            f"/api/invoices/{created['id']}",
            json={
                "lines": [
                    {
                        "description": "Cours de soutien",
                        "line_type": "cours",
                        "quantity": "1",
                        "unit_price": "150.00",
                    }
                ]
            },
            headers=auth_headers,
        )

        assert update_response.status_code == 200
        assert update_response.json()["total_amount"] == "150.00"

        regenerated_entries = list(
            (
                await db_session.execute(
                    select(AccountingEntry)
                    .where(AccountingEntry.source_type == EntrySourceType.INVOICE)
                    .where(AccountingEntry.source_id == created["id"])
                    .order_by(AccountingEntry.entry_number.asc())
                )
            ).scalars()
        )
        assert len(regenerated_entries) == 2
        assert any(entry.debit == Decimal("150.00") for entry in regenerated_entries)
        assert any(entry.credit == Decimal("150.00") for entry in regenerated_entries)

    async def test_update_paid_invoice_returns_conflict(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(
            client,
            auth_headers,
            cid,
            lines=[
                {
                    "description": "Cours de soutien",
                    "line_type": "cours",
                    "quantity": "1",
                    "unit_price": "130.00",
                }
            ],
        )
        await client.patch(
            f"/api/invoices/{created['id']}/status",
            json={"status": "sent"},
            headers=auth_headers,
        )
        payment_response = await client.post(
            "/api/payments/",
            json={
                "invoice_id": created["id"],
                "contact_id": cid,
                "amount": "130.00",
                "date": "2025-09-02",
                "method": "cheque",
            },
            headers=auth_headers,
        )
        assert payment_response.status_code == 201

        update_response = await client.put(
            f"/api/invoices/{created['id']}",
            json={"description": "Updated"},
            headers=auth_headers,
        )

        assert update_response.status_code == 409


class TestStatusChange:
    async def test_draft_to_sent(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(client, auth_headers, cid)
        r = await client.patch(
            f"/api/invoices/{created['id']}/status",
            json={"status": "sent"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "sent"

    async def test_invalid_transition_returns_409(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(client, auth_headers, cid)
        await client.patch(
            f"/api/invoices/{created['id']}/status",
            json={"status": "paid"},
            headers=auth_headers,
        )
        r = await client.patch(
            f"/api/invoices/{created['id']}/status",
            json={"status": "sent"},
            headers=auth_headers,
        )
        assert r.status_code == 409

    async def test_sent_client_cs_a_invoice_splits_entries_from_user_lines(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session,
    ):
        await seed_default_rules(db_session)
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(
            client,
            auth_headers,
            cid,
            lines=[
                {
                    "description": "Cours de soutien",
                    "line_type": "cours",
                    "quantity": "1",
                    "unit_price": "130.00",
                },
                {
                    "description": "Adhesion annuelle",
                    "line_type": "adhesion",
                    "quantity": "1",
                    "unit_price": "30.00",
                },
            ],
        )

        r = await client.patch(
            f"/api/invoices/{created['id']}/status",
            json={"status": "sent"},
            headers=auth_headers,
        )

        assert r.status_code == 200
        entries = list(
            (
                await db_session.execute(
                    select(AccountingEntry)
                    .where(AccountingEntry.source_type == EntrySourceType.INVOICE)
                    .where(AccountingEntry.source_id == created["id"])
                    .order_by(AccountingEntry.entry_number.asc())
                )
            ).scalars()
        )
        assert len(entries) == 3
        assert any(
            entry.account_number == "411100" and entry.debit == Decimal("160.00")
            for entry in entries
        )
        assert any(
            entry.account_number == "706110" and entry.credit == Decimal("130.00")
            for entry in entries
        )
        assert any(
            entry.account_number == "756000" and entry.credit == Decimal("30.00")
            for entry in entries
        )


class TestDuplicate:
    async def test_duplicate_creates_new_draft(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        original = await _create_invoice(client, auth_headers, cid)
        r = await client.post(f"/api/invoices/{original['id']}/duplicate", headers=auth_headers)
        assert r.status_code == 201
        copy = r.json()
        assert copy["status"] == "draft"
        assert copy["number"] != original["number"]
        assert copy["contact_id"] == original["contact_id"]


class TestDeleteInvoice:
    async def test_delete_draft(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(client, auth_headers, cid)
        r = await client.delete(f"/api/invoices/{created['id']}", headers=auth_headers)
        assert r.status_code == 204
        r2 = await client.get(f"/api/invoices/{created['id']}", headers=auth_headers)
        assert r2.status_code == 404

    async def test_cannot_delete_sent_invoice(self, client: AsyncClient, auth_headers: dict):
        cid = await _create_contact(client, auth_headers)
        created = await _create_invoice(client, auth_headers, cid)
        await client.patch(
            f"/api/invoices/{created['id']}/status",
            json={"status": "sent"},
            headers=auth_headers,
        )
        r = await client.delete(f"/api/invoices/{created['id']}", headers=auth_headers)
        assert r.status_code == 409
