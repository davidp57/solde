"""Unit tests for the settings service."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_rule import (
    AccountingRule,
    AccountingRuleEntry,
    EntrySide,
    TriggerType,
)
from backend.models.app_settings import AppSettings
from backend.models.bank import BankTransaction, BankTransactionSource
from backend.models.cash import CashMovementType, CashRegister
from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.import_log import ImportLog, ImportLogStatus, ImportLogType
from backend.models.user import User, UserRole
from backend.schemas.settings import (
    AppSettingsUpdate,
    SystemOpeningUpdate,
    TreasurySystemOpeningUpdate,
)
from backend.services.settings import (
    bootstrap_accounting_setup,
    get_settings,
    get_treasury_system_opening,
    reset_data,
    update_settings,
    upsert_treasury_system_opening,
)


class TestGetSettings:
    async def test_returns_defaults_when_no_row_exists(self, db_session: AsyncSession):
        settings = await get_settings(db_session)

        assert settings.id == 1
        assert settings.association_name == "Mon Association"
        assert settings.fiscal_year_start_month == 8
        assert settings.smtp_host is None
        assert settings.smtp_port == 587
        assert settings.smtp_use_tls is True

    async def test_creates_row_on_first_call(self, db_session: AsyncSession):
        await get_settings(db_session)
        # Second call should return the same row, not create a duplicate
        settings = await get_settings(db_session)
        assert settings.id == 1

    async def test_returns_persisted_values(self, db_session: AsyncSession):
        settings = await get_settings(db_session)
        settings.association_name = "Test Asso"
        await db_session.commit()

        reloaded = await get_settings(db_session)
        assert reloaded.association_name == "Test Asso"


class TestUpdateSettings:
    async def test_partial_update_association_name(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(association_name="Nouvelle Asso")
        settings = await update_settings(db_session, payload)

        assert settings.association_name == "Nouvelle Asso"
        # Other fields unchanged
        assert settings.fiscal_year_start_month == 8

    async def test_update_smtp_fields(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(
            smtp_host="smtp.example.com",
            smtp_port=465,
            smtp_user="user@example.com",
            smtp_password="secret",
            smtp_from_email="noreply@example.com",
            smtp_use_tls=False,
        )
        settings = await update_settings(db_session, payload)

        assert settings.smtp_host == "smtp.example.com"
        assert settings.smtp_port == 465
        assert settings.smtp_user == "user@example.com"
        assert settings.smtp_from_email == "noreply@example.com"
        assert settings.smtp_use_tls is False

    async def test_update_fiscal_year_start_month(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(fiscal_year_start_month=1)
        settings = await update_settings(db_session, payload)
        assert settings.fiscal_year_start_month == 1

    async def test_excludes_unset_fields(self, db_session: AsyncSession):
        # Set initial state
        await update_settings(
            db_session, AppSettingsUpdate(association_name="Asso A", smtp_port=465)
        )

        # Update only one field — the other must remain unchanged
        settings = await update_settings(db_session, AppSettingsUpdate(association_name="Asso B"))
        assert settings.association_name == "Asso B"
        assert settings.smtp_port == 465

    async def test_creates_row_if_not_exists(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(association_name="Nouvelle Asso")
        settings = await update_settings(db_session, payload)
        assert settings.id == 1


class TestResetData:
    async def test_reset_data_deletes_everything_except_users(
        self, db_session: AsyncSession
    ) -> None:
        settings = await get_settings(db_session)
        settings.association_name = "Asso supprimée"

        db_session.add(
            User(
                username="admin",
                email="admin@test.com",
                password_hash="hashed-password",
                role=UserRole.ADMIN,
                is_active=True,
            )
        )
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

        db_session.add(Contact(nom="Dupont", type=ContactType.CLIENT))
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

        deleted = await reset_data(db_session)

        assert deleted["contacts"] == 1
        assert deleted["import_logs"] == 1
        assert deleted["app_settings"] == 1
        assert deleted["accounting_accounts"] == 1
        assert deleted["accounting_rules"] == 1
        assert deleted["accounting_rule_entries"] == 1
        assert deleted["fiscal_years"] == 1
        assert (await db_session.execute(select(Contact))).scalars().all() == []
        assert (await db_session.execute(select(ImportLog))).scalars().all() == []
        assert (await db_session.execute(select(AppSettings))).scalars().all() == []
        assert (await db_session.execute(select(AccountingAccount))).scalars().all() == []
        assert (await db_session.execute(select(AccountingRule))).scalars().all() == []
        assert (await db_session.execute(select(AccountingRuleEntry))).scalars().all() == []
        assert (await db_session.execute(select(FiscalYear))).scalars().all() == []
        users = (await db_session.execute(select(User))).scalars().all()
        assert len(users) == 1
        assert users[0].username == "admin"

        reloaded_settings = await get_settings(db_session)
        assert reloaded_settings.association_name == "Mon Association"


class TestBootstrapAccountingSetup:
    async def test_bootstrap_accounting_setup_seeds_reference_data(
        self, db_session: AsyncSession
    ) -> None:
        summary = await bootstrap_accounting_setup(db_session)

        accounts = (await db_session.execute(select(AccountingAccount))).scalars().all()
        rules = (await db_session.execute(select(AccountingRule))).scalars().all()
        fiscal_years = (
            (await db_session.execute(select(FiscalYear).order_by(FiscalYear.start_date.asc())))
            .scalars()
            .all()
        )

        assert summary["accounts_inserted"] > 0
        assert summary["rules_inserted"] > 0
        assert summary["fiscal_years_created"] == 3
        assert len(accounts) >= 1
        assert len(rules) >= 1
        assert [(fy.name, fy.start_date, fy.end_date) for fy in fiscal_years] == [
            ("2023", date(2023, 8, 1), date(2024, 7, 31)),
            ("2024", date(2024, 8, 1), date(2025, 7, 31)),
            ("2025", date(2025, 8, 1), date(2026, 7, 31)),
        ]

    async def test_bootstrap_accounting_setup_is_idempotent(self, db_session: AsyncSession) -> None:
        await bootstrap_accounting_setup(db_session)

        summary = await bootstrap_accounting_setup(db_session)

        assert summary == {
            "accounts_inserted": 0,
            "rules_inserted": 0,
            "fiscal_years_created": 0,
        }


class TestTreasurySystemOpening:
    async def test_returns_oldest_fiscal_year_start_as_default_date(
        self, db_session: AsyncSession
    ) -> None:
        db_session.add_all(
            [
                FiscalYear(
                    name="2024",
                    start_date=date(2024, 8, 1),
                    end_date=date(2025, 7, 31),
                    status=FiscalYearStatus.OPEN,
                ),
                FiscalYear(
                    name="2025",
                    start_date=date(2025, 8, 1),
                    end_date=date(2026, 7, 31),
                    status=FiscalYearStatus.OPEN,
                ),
            ]
        )
        await db_session.commit()

        opening = await get_treasury_system_opening(db_session)

        assert opening.default_date == date(2024, 8, 1)
        assert opening.bank.configured is False
        assert opening.cash.configured is False

    async def test_upsert_creates_openings_and_recomputes_running_balances(
        self, db_session: AsyncSession
    ) -> None:
        bank_tx = BankTransaction(
            date=date(2024, 8, 2),
            amount=Decimal("10.00"),
            reference="RELEVE-1",
            description="Operation courante",
            balance_after=Decimal("10.00"),
            source=BankTransactionSource.IMPORT,
        )
        cash_entry = CashRegister(
            date=date(2024, 8, 2),
            amount=Decimal("30.00"),
            type=CashMovementType.IN,
            reference="CAISSE-1",
            description="Recette",
            balance_after=Decimal("30.00"),
        )
        db_session.add_all([bank_tx, cash_entry])
        await db_session.commit()

        opening = await upsert_treasury_system_opening(
            db_session,
            TreasurySystemOpeningUpdate(
                bank=SystemOpeningUpdate(
                    date=date(2024, 8, 1),
                    amount=Decimal("100.00"),
                    reference="Solde banque initial",
                ),
                cash=SystemOpeningUpdate(
                    date=date(2024, 8, 1),
                    amount=Decimal("50.00"),
                    reference="Fond de caisse initial",
                ),
            ),
        )

        assert opening.bank.configured is True
        assert opening.bank.amount == Decimal("100.00")
        assert opening.cash.configured is True
        assert opening.cash.amount == Decimal("50.00")

        bank_entries = (
            (
                await db_session.execute(
                    select(BankTransaction).order_by(BankTransaction.date, BankTransaction.id)
                )
            )
            .scalars()
            .all()
        )
        cash_entries = (
            (
                await db_session.execute(
                    select(CashRegister).order_by(CashRegister.date, CashRegister.id)
                )
            )
            .scalars()
            .all()
        )

        assert len(bank_entries) == 2
        assert bank_entries[0].source == BankTransactionSource.SYSTEM_OPENING
        assert bank_entries[0].balance_after == Decimal("100.00")
        assert bank_entries[1].balance_after == Decimal("110.00")

        assert len(cash_entries) == 2
        assert cash_entries[0].description == "Ouverture du système"
        assert cash_entries[0].balance_after == Decimal("50.00")
        assert cash_entries[1].balance_after == Decimal("80.00")

    async def test_upsert_updates_existing_openings_without_duplication(
        self, db_session: AsyncSession
    ) -> None:
        await upsert_treasury_system_opening(
            db_session,
            TreasurySystemOpeningUpdate(
                bank=SystemOpeningUpdate(date=date(2024, 8, 1), amount=Decimal("100.00")),
                cash=SystemOpeningUpdate(date=date(2024, 8, 1), amount=Decimal("20.00")),
            ),
        )

        opening = await upsert_treasury_system_opening(
            db_session,
            TreasurySystemOpeningUpdate(
                bank=SystemOpeningUpdate(date=date(2024, 8, 1), amount=Decimal("125.00")),
                cash=SystemOpeningUpdate(date=date(2024, 8, 1), amount=Decimal("-10.00")),
            ),
        )

        bank_entries = (await db_session.execute(select(BankTransaction))).scalars().all()
        cash_entries = (await db_session.execute(select(CashRegister))).scalars().all()

        assert len(bank_entries) == 1
        assert len(cash_entries) == 1
        assert opening.bank.amount == Decimal("125.00")
        assert opening.cash.amount == Decimal("-10.00")
        assert cash_entries[0].type == CashMovementType.OUT
        assert cash_entries[0].amount == Decimal("10.00")
