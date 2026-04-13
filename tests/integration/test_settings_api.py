"""Integration tests for GET/PUT /api/settings."""

from httpx import AsyncClient
from sqlalchemy import select


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


class TestNonAdminAccess:
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
