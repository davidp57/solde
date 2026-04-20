"""Integration tests for GET/PUT /api/settings."""

import json
from datetime import date
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.bank import BankTransaction, BankTransactionSource
from backend.models.cash import CashEntrySource, CashMovementType, CashRegister
from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.import_log import ImportLog, ImportLogStatus, ImportLogType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import PaymentMethod
from backend.schemas.bank import DepositCreate
from backend.schemas.payment import PaymentCreate
from backend.services import bank_service
from backend.services import payment as payment_service


class TestGetSettings:
    async def test_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/settings/")
        assert response.status_code == 401

    async def test_requires_admin_role(self, client: AsyncClient, auth_headers: dict):
        # auth_headers fixture uses an ADMIN user, so this should succeed
        response = await client.get("/api/settings/", headers=auth_headers)
        assert response.status_code == 200

    async def test_returns_default_settings(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/settings/", headers=auth_headers)
        data = response.json()

        assert data["association_name"] == "Mon Association"
        assert data["fiscal_year_start_month"] == 8
        assert data["smtp_host"] is None
        assert data["smtp_port"] == 587
        assert data["smtp_use_tls"] is True

    async def test_does_not_expose_smtp_password(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/settings/", headers=auth_headers)
        data = response.json()
        assert "smtp_password" not in data


class TestUpdateSettings:
    async def test_requires_auth(self, client: AsyncClient):
        response = await client.put("/api/settings/", json={"association_name": "X"})
        assert response.status_code == 401

    async def test_update_association_name(self, client: AsyncClient, auth_headers: dict):
        response = await client.put(
            "/api/settings/",
            json={"association_name": "Soutien Scolaire Test"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["association_name"] == "Soutien Scolaire Test"

    async def test_update_persists(self, client: AsyncClient, auth_headers: dict):
        await client.put(
            "/api/settings/",
            json={"association_name": "Asso Persistée"},
            headers=auth_headers,
        )
        response = await client.get("/api/settings/", headers=auth_headers)
        assert response.json()["association_name"] == "Asso Persistée"

    async def test_partial_update_preserves_other_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        # First update
        await client.put(
            "/api/settings/",
            json={"fiscal_year_start_month": 9, "association_name": "Asso Testing"},
            headers=auth_headers,
        )
        # Second partial update — only one field
        await client.put(
            "/api/settings/",
            json={"association_name": "Asso Updated"},
            headers=auth_headers,
        )
        response = await client.get("/api/settings/", headers=auth_headers)
        data = response.json()
        assert data["association_name"] == "Asso Updated"
        assert data["fiscal_year_start_month"] == 9  # unchanged

    async def test_invalid_fiscal_year_month(self, client: AsyncClient, auth_headers: dict):
        response = await client.put(
            "/api/settings/",
            json={"fiscal_year_start_month": 13},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_invalid_smtp_port(self, client: AsyncClient, auth_headers: dict):
        response = await client.put(
            "/api/settings/",
            json={"smtp_port": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_update_smtp_settings(self, client: AsyncClient, auth_headers: dict):
        response = await client.put(
            "/api/settings/",
            json={
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_user": "test@gmail.com",
                "smtp_from_email": "noreply@test.com",
                "smtp_use_tls": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["smtp_host"] == "smtp.gmail.com"
        assert data["smtp_user"] == "test@gmail.com"


class TestTreasurySystemOpening:
    async def test_get_system_opening_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/settings/system-opening")
        assert response.status_code == 401

    async def test_get_system_opening_returns_default_date(
        self, client: AsyncClient, auth_headers: dict, db_session
    ) -> None:
        db_session.add(
            FiscalYear(
                name="2024",
                start_date=date(2024, 8, 1),
                end_date=date(2025, 7, 31),
                status=FiscalYearStatus.OPEN,
            )
        )
        await db_session.commit()

        response = await client.get("/api/settings/system-opening", headers=auth_headers)

        assert response.status_code == 200
        payload = response.json()
        assert payload["default_date"] == "2024-08-01"
        assert payload["bank"]["configured"] is False
        assert payload["cash"]["configured"] is False

    async def test_put_system_opening_creates_bank_and_cash_entries(
        self, client: AsyncClient, auth_headers: dict, db_session
    ) -> None:
        response = await client.put(
            "/api/settings/system-opening",
            json={
                "bank": {
                    "date": "2024-08-01",
                    "amount": "100.00",
                    "reference": "Solde banque initial",
                },
                "cash": {
                    "date": "2024-08-01",
                    "amount": "-15.00",
                    "reference": "Ajustement initial",
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["bank"]["configured"] is True
        assert payload["bank"]["amount"] == "100.00"
        assert payload["cash"]["configured"] is True
        assert payload["cash"]["amount"] == "-15.00"

        bank_entry = (await db_session.execute(select(BankTransaction))).scalar_one()
        cash_entry = (await db_session.execute(select(CashRegister))).scalar_one()

        assert bank_entry.source == BankTransactionSource.SYSTEM_OPENING
        assert bank_entry.reference == "Solde banque initial"
        assert cash_entry.source == CashEntrySource.SYSTEM_OPENING
        assert cash_entry.type == CashMovementType.OUT
        assert cash_entry.amount == 15
        assert cash_entry.reference == "Ajustement initial"


class TestNonAdminAccess:
    async def test_tresorier_cannot_access_system_opening_get(
        self, client: AsyncClient, db_session, auth_headers: dict
    ):
        from backend.models.user import User, UserRole
        from backend.services.auth import hash_password

        tresorier = User(
            username="tresorier-system-opening-read",
            email="tresorier-system-opening-read@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.TRESORIER,
            is_active=True,
        )
        db_session.add(tresorier)
        await db_session.commit()

        login = await client.post(
            "/api/auth/login",
            data={"username": "tresorier-system-opening-read", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = await client.get("/api/settings/system-opening", headers=headers)
        assert response.status_code == 403

    async def test_tresorier_cannot_access_system_opening_put(
        self, client: AsyncClient, db_session, auth_headers: dict
    ):
        from backend.models.user import User, UserRole
        from backend.services.auth import hash_password

        tresorier = User(
            username="tresorier-system-opening-write",
            email="tresorier-system-opening-write@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.TRESORIER,
            is_active=True,
        )
        db_session.add(tresorier)
        await db_session.commit()

        login = await client.post(
            "/api/auth/login",
            data={"username": "tresorier-system-opening-write", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = await client.put(
            "/api/settings/system-opening",
            json={
                "bank": {"date": "2024-08-01", "amount": "100.00"},
                "cash": {"date": "2024-08-01", "amount": "50.00"},
            },
            headers=headers,
        )
        assert response.status_code == 403

    async def test_tresorier_cannot_access_settings(
        self, client: AsyncClient, db_session, auth_headers: dict
    ):
        from backend.models.user import User, UserRole
        from backend.services.auth import hash_password

        tresorier = User(
            username="tresorier",
            email="tresorier@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.TRESORIER,
            is_active=True,
        )
        db_session.add(tresorier)
        await db_session.commit()

        login = await client.post(
            "/api/auth/login",
            data={"username": "tresorier", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = await client.get("/api/settings/", headers=headers)
        assert response.status_code == 403


class TestResetDatabase:
    async def test_reset_db_deletes_everything_except_users(
        self, client: AsyncClient, auth_headers: dict, db_session
    ) -> None:
        from datetime import date

        from backend.models.accounting_account import AccountingAccount, AccountType
        from backend.models.accounting_rule import (
            AccountingRule,
            AccountingRuleEntry,
            EntrySide,
            TriggerType,
        )
        from backend.models.app_settings import AppSettings
        from backend.models.contact import Contact, ContactType
        from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
        from backend.models.import_log import ImportLog, ImportLogStatus, ImportLogType
        from backend.models.user import User

        db_session.add(AppSettings(id=1, association_name="Asso supprimée"))
        db_session.add(Contact(nom="Dupont", type=ContactType.CLIENT))
        db_session.add(
            AccountingAccount(
                number="706110",
                label="Cours de soutien",
                type=AccountType.PRODUIT,
                is_default=False,
                is_active=True,
            )
        )
        rule = AccountingRule(
            name="Rule",
            trigger_type=TriggerType.INVOICE_CLIENT_CS,
            is_active=True,
            priority=10,
        )
        db_session.add(rule)
        await db_session.flush()
        db_session.add(
            AccountingRuleEntry(
                rule_id=rule.id,
                account_number="706110",
                side=EntrySide.CREDIT,
                description_template="{{label}}",
            )
        )
        db_session.add(
            FiscalYear(
                name="2025",
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                status=FiscalYearStatus.OPEN,
            )
        )
        db_session.add(
            ImportLog(
                import_type=ImportLogType.GESTION,
                status=ImportLogStatus.SUCCESS,
                file_hash="hash-1",
                file_name="Gestion 2025.xlsx",
                summary="{}",
            )
        )
        await db_session.commit()
        user_count = len((await db_session.execute(select(User))).scalars().all())

        response = await client.post("/api/settings/reset-db", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["contacts"] == 1
        assert response.json()["import_logs"] == 1
        assert response.json()["app_settings"] == 1
        assert response.json()["accounting_accounts"] == 1
        assert response.json()["accounting_rules"] == 1
        assert response.json()["accounting_rule_entries"] == 1
        assert response.json()["fiscal_years"] == 1
        assert (await db_session.execute(select(Contact))).scalars().all() == []
        assert (await db_session.execute(select(ImportLog))).scalars().all() == []
        assert (await db_session.execute(select(AppSettings))).scalars().all() == []
        assert (await db_session.execute(select(AccountingAccount))).scalars().all() == []
        assert (await db_session.execute(select(AccountingRule))).scalars().all() == []
        assert (await db_session.execute(select(AccountingRuleEntry))).scalars().all() == []
        assert (await db_session.execute(select(FiscalYear))).scalars().all() == []
        assert len((await db_session.execute(select(User))).scalars().all()) == user_count

        settings_response = await client.get("/api/settings/", headers=auth_headers)
        assert settings_response.status_code == 200
        assert settings_response.json()["association_name"] == "Mon Association"


class TestSelectiveReset:
    async def test_selective_reset_preview_and_apply_for_gestion(
        self, client: AsyncClient, auth_headers: dict, db_session
    ) -> None:
        fiscal_year = FiscalYear(
            name="2025",
            start_date=date(2025, 8, 1),
            end_date=date(2026, 7, 31),
            status=FiscalYearStatus.OPEN,
        )
        imported_contact = Contact(nom="Lopes", type=ContactType.CLIENT)
        db_session.add_all([fiscal_year, imported_contact])
        await db_session.flush()

        imported_invoice = Invoice(
            number="2025-C-0100",
            type=InvoiceType.CLIENT,
            contact_id=imported_contact.id,
            date=date(2025, 9, 12),
            total_amount=Decimal("90.00"),
            paid_amount=Decimal("0.00"),
            status=InvoiceStatus.SENT,
        )
        db_session.add(imported_invoice)
        await db_session.flush()

        db_session.add(
            ImportLog(
                import_type=ImportLogType.GESTION,
                status=ImportLogStatus.SUCCESS,
                file_hash="gestion-preview-2025",
                file_name="Gestion 2025.xlsx",
                summary=json.dumps(
                    {
                        "created_objects": [
                            {
                                "sheet_name": "Factures",
                                "kind": "contacts",
                                "object_type": "contact",
                                "object_id": imported_contact.id,
                            },
                            {
                                "sheet_name": "Factures",
                                "kind": "invoices",
                                "object_type": "invoice",
                                "object_id": imported_invoice.id,
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
            )
        )
        await db_session.commit()

        payment = await payment_service.create_payment(
            db_session,
            PaymentCreate(
                invoice_id=imported_invoice.id,
                contact_id=imported_contact.id,
                amount=Decimal("90.00"),
                date=date(2025, 9, 20),
                method=PaymentMethod.ESPECES,
            ),
        )
        deposit = await bank_service.create_deposit(
            db_session,
            DepositCreate(
                date=date(2025, 9, 28),
                type="especes",
                payment_ids=[payment.id],
            ),
        )
        db_session.add(
            AccountingEntry(
                entry_number="000301",
                date=payment.date,
                account_number="530000",
                label="Paiement derive API",
                debit=Decimal("90.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=fiscal_year.id,
                source_type=EntrySourceType.PAYMENT,
                source_id=payment.id,
            )
        )
        await db_session.commit()

        preview_response = await client.post(
            "/api/settings/selective-reset/preview",
            json={"import_type": "gestion", "fiscal_year_id": fiscal_year.id},
            headers=auth_headers,
        )

        assert preview_response.status_code == 200
        preview_payload = preview_response.json()
        assert preview_payload["matched_import_logs"] == 1
        assert preview_payload["delete_plan"]["invoice"] == 1
        assert preview_payload["delete_plan"]["payment"] == 1
        assert preview_payload["delete_plan"]["deposit"] == 1

        apply_response = await client.post(
            "/api/settings/selective-reset/apply",
            json={"import_type": "gestion", "fiscal_year_id": fiscal_year.id},
            headers=auth_headers,
        )

        assert apply_response.status_code == 200
        assert (await db_session.get(Contact, imported_contact.id)) is None
        assert (await db_session.get(Invoice, imported_invoice.id)) is None
        assert (await db_session.get(type(deposit), deposit.id)) is None
        assert (await db_session.execute(select(ImportLog))).scalars().all() == []


class TestBootstrapAccountingSetup:
    async def test_bootstrap_accounting_setup_endpoint(
        self, client: AsyncClient, auth_headers: dict, db_session
    ) -> None:
        from datetime import date

        from backend.models.accounting_account import AccountingAccount
        from backend.models.accounting_rule import AccountingRule
        from backend.models.fiscal_year import FiscalYear

        response = await client.post("/api/settings/bootstrap-accounting", headers=auth_headers)

        assert response.status_code == 200
        payload = response.json()
        assert payload["accounts_inserted"] > 0
        assert payload["rules_inserted"] > 0
        assert payload["fiscal_years_created"] == 3

        assert (await db_session.execute(select(AccountingAccount))).scalars().first() is not None
        assert (await db_session.execute(select(AccountingRule))).scalars().first() is not None
        fiscal_years = (
            (await db_session.execute(select(FiscalYear).order_by(FiscalYear.start_date.asc())))
            .scalars()
            .all()
        )
        assert [(fy.name, fy.start_date, fy.end_date) for fy in fiscal_years] == [
            ("2023", date(2023, 8, 1), date(2024, 7, 31)),
            ("2024", date(2024, 8, 1), date(2025, 7, 31)),
            ("2025", date(2025, 8, 1), date(2026, 7, 31)),
        ]
