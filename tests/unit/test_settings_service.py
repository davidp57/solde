"""Unit tests for the settings service."""

import json
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.accounting_rule import (
    AccountingRule,
    AccountingRuleEntry,
    EntrySide,
    TriggerType,
)
from backend.models.app_settings import AppSettings
from backend.models.bank import BankTransaction, BankTransactionSource
from backend.models.cash import (
    CASH_SYSTEM_OPENING_DESCRIPTION,
    CashEntrySource,
    CashMovementType,
    CashRegister,
)
from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.import_log import ImportLog, ImportLogStatus, ImportLogType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import PaymentMethod
from backend.models.user import User, UserRole
from backend.schemas.bank import DepositCreate
from backend.schemas.payment import PaymentCreate
from backend.schemas.settings import (
    AppSettingsUpdate,
    SelectiveResetRequest,
    SystemOpeningUpdate,
    TreasurySystemOpeningUpdate,
)
from backend.services import bank_service
from backend.services import payment as payment_service
from backend.services.bank_service import recompute_bank_balances
from backend.services.cash_service import recompute_cash_balances
from backend.services.settings import (
    apply_selective_reset,
    bootstrap_accounting_setup,
    get_settings,
    get_treasury_system_opening,
    preview_selective_reset,
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
        assert settings.default_invoice_due_days is None
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

    async def test_update_default_invoice_due_days(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(default_invoice_due_days=30)
        settings = await update_settings(db_session, payload)

        assert settings.default_invoice_due_days == 30

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


class TestSelectiveReset:
    async def test_preview_selective_reset_raises_lookup_error_for_unknown_fiscal_year(
        self,
        db_session: AsyncSession,
    ) -> None:
        with pytest.raises(LookupError, match="Fiscal year not found"):
            await preview_selective_reset(
                db_session,
                SelectiveResetRequest(import_type=ImportLogType.GESTION, fiscal_year_id=999999),
            )

    async def test_preview_and_apply_selective_reset_for_gestion_with_solde_derivatives(
        self,
        db_session: AsyncSession,
    ) -> None:
        fiscal_year = FiscalYear(
            name="2025",
            start_date=date(2025, 8, 1),
            end_date=date(2026, 7, 31),
            status=FiscalYearStatus.OPEN,
        )
        imported_contact = Contact(nom="Lopes", prenom="Christine", type=ContactType.CLIENT)
        unrelated_contact = Contact(nom="Martin", prenom="Luc", type=ContactType.CLIENT)
        db_session.add_all([fiscal_year, imported_contact, unrelated_contact])
        await db_session.flush()

        imported_invoice = Invoice(
            number="2025-C-0001",
            type=InvoiceType.CLIENT,
            contact_id=imported_contact.id,
            date=date(2025, 9, 10),
            total_amount=Decimal("120.00"),
            paid_amount=Decimal("0.00"),
            status=InvoiceStatus.SENT,
        )
        unrelated_invoice = Invoice(
            number="2025-C-0002",
            type=InvoiceType.CLIENT,
            contact_id=unrelated_contact.id,
            date=date(2025, 10, 5),
            total_amount=Decimal("80.00"),
            paid_amount=Decimal("0.00"),
            status=InvoiceStatus.SENT,
        )
        db_session.add_all([imported_invoice, unrelated_invoice])
        await db_session.flush()

        db_session.add(
            ImportLog(
                import_type=ImportLogType.GESTION,
                status=ImportLogStatus.SUCCESS,
                file_hash="gestion-2025-hash",
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

        derived_payment = await payment_service.create_payment(
            db_session,
            PaymentCreate(
                invoice_id=imported_invoice.id,
                contact_id=imported_contact.id,
                amount=Decimal("120.00"),
                date=date(2025, 9, 20),
                method=PaymentMethod.ESPECES,
                reference="REG-2025-001",
            ),
        )
        deposit = await bank_service.create_deposit(
            db_session,
            DepositCreate(
                date=date(2025, 9, 25),
                type="especes",
                payment_ids=[derived_payment.id],
                bank_reference="DEP-2025-001",
            ),
        )

        db_session.add_all(
            [
                AccountingEntry(
                    entry_number="000101",
                    date=imported_invoice.date,
                    account_number="411000",
                    label="Facture importee",
                    debit=Decimal("120.00"),
                    credit=Decimal("0.00"),
                    fiscal_year_id=fiscal_year.id,
                    source_type=EntrySourceType.INVOICE,
                    source_id=imported_invoice.id,
                ),
                AccountingEntry(
                    entry_number="000102",
                    date=derived_payment.date,
                    account_number="512100",
                    label="Paiement derive",
                    debit=Decimal("0.00"),
                    credit=Decimal("120.00"),
                    fiscal_year_id=fiscal_year.id,
                    source_type=EntrySourceType.PAYMENT,
                    source_id=derived_payment.id,
                ),
                AccountingEntry(
                    entry_number="000103",
                    date=deposit.date,
                    account_number="530000",
                    label="Remise derivee",
                    debit=Decimal("0.00"),
                    credit=Decimal("120.00"),
                    fiscal_year_id=fiscal_year.id,
                    source_type=EntrySourceType.DEPOSIT,
                    source_id=deposit.id,
                ),
                AccountingEntry(
                    entry_number="000104",
                    date=unrelated_invoice.date,
                    account_number="411000",
                    label="Manuelle hors scope",
                    debit=Decimal("80.00"),
                    credit=Decimal("0.00"),
                    fiscal_year_id=fiscal_year.id,
                    source_type=EntrySourceType.MANUAL,
                    source_id=999,
                ),
            ]
        )
        await db_session.commit()

        preview = await preview_selective_reset(
            db_session,
            SelectiveResetRequest(import_type=ImportLogType.GESTION, fiscal_year_id=fiscal_year.id),
        )

        assert preview.matched_import_logs == 1
        assert preview.root_objects["contact"] == 1
        assert preview.root_objects["invoice"] == 1
        assert preview.derived_objects["payment"] == 1
        assert preview.delete_plan["deposit"] == 1
        assert preview.delete_plan["cash_register"] == 2
        assert preview.delete_plan["accounting_entry"] == 3
        assert preview.delete_plan["contact"] == 1

        applied = await apply_selective_reset(
            db_session,
            SelectiveResetRequest(import_type=ImportLogType.GESTION, fiscal_year_id=fiscal_year.id),
        )

        assert applied.delete_plan["invoice"] == 1
        assert applied.delete_plan["payment"] == 1
        assert applied.delete_plan["deposit"] == 1
        assert applied.delete_plan["import_logs"] == 1
        assert (await db_session.get(Contact, imported_contact.id)) is None
        assert (await db_session.get(Invoice, imported_invoice.id)) is None
        assert (await db_session.get(type(deposit), deposit.id)) is None
        assert (await db_session.get(Contact, unrelated_contact.id)) is not None
        assert (await db_session.get(Invoice, unrelated_invoice.id)) is not None
        remaining_entries = (await db_session.execute(select(AccountingEntry))).scalars().all()
        assert [entry.entry_number for entry in remaining_entries] == ["000104"]
        remaining_cash_entries = (await db_session.execute(select(CashRegister))).scalars().all()
        assert remaining_cash_entries == []
        remaining_logs = (await db_session.execute(select(ImportLog))).scalars().all()
        assert remaining_logs == []

    async def test_apply_selective_reset_for_comptabilite_preserves_manual_entries(
        self,
        db_session: AsyncSession,
    ) -> None:
        fiscal_year = FiscalYear(
            name="2025",
            start_date=date(2025, 8, 1),
            end_date=date(2026, 7, 31),
            status=FiscalYearStatus.OPEN,
        )
        db_session.add(fiscal_year)
        await db_session.flush()

        imported_entry = AccountingEntry(
            entry_number="000201",
            date=date(2025, 11, 1),
            account_number="606100",
            label="Import compta",
            debit=Decimal("25.00"),
            credit=Decimal("0.00"),
            fiscal_year_id=fiscal_year.id,
            source_type=EntrySourceType.MANUAL,
            source_id=5001,
        )
        manual_entry = AccountingEntry(
            entry_number="000202",
            date=date(2025, 11, 2),
            account_number="606200",
            label="Saisie manuelle",
            debit=Decimal("30.00"),
            credit=Decimal("0.00"),
            fiscal_year_id=fiscal_year.id,
            source_type=EntrySourceType.MANUAL,
            source_id=5002,
        )
        db_session.add_all([imported_entry, manual_entry])
        await db_session.flush()
        db_session.add(
            ImportLog(
                import_type=ImportLogType.COMPTABILITE,
                status=ImportLogStatus.SUCCESS,
                file_hash="compta-2025-hash",
                file_name="Comptabilite 2025.xlsx",
                summary=json.dumps(
                    {
                        "created_objects": [
                            {
                                "sheet_name": "Journal",
                                "kind": "entries",
                                "object_type": "accounting_entry",
                                "object_id": imported_entry.id,
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
            )
        )
        await db_session.commit()

        preview = await preview_selective_reset(
            db_session,
            SelectiveResetRequest(
                import_type=ImportLogType.COMPTABILITE,
                fiscal_year_id=fiscal_year.id,
            ),
        )

        assert preview.delete_plan["accounting_entry"] == 1
        assert preview.delete_plan["import_logs"] == 1

        await apply_selective_reset(
            db_session,
            SelectiveResetRequest(
                import_type=ImportLogType.COMPTABILITE,
                fiscal_year_id=fiscal_year.id,
            ),
        )

        remaining_entries = (await db_session.execute(select(AccountingEntry))).scalars().all()
        assert [entry.entry_number for entry in remaining_entries] == ["000202"]


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
        assert cash_entries[0].description == CASH_SYSTEM_OPENING_DESCRIPTION
        assert cash_entries[0].source == CashEntrySource.SYSTEM_OPENING
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
        opening_bank_entries = [
            entry for entry in bank_entries if entry.source == BankTransactionSource.SYSTEM_OPENING
        ]
        assert len(opening_bank_entries) == 1

    async def test_upsert_moving_opening_dates_recomputes_running_balances(
        self, db_session: AsyncSession
    ) -> None:
        await upsert_treasury_system_opening(
            db_session,
            TreasurySystemOpeningUpdate(
                bank=SystemOpeningUpdate(date=date(2024, 8, 2), amount=Decimal("100.00")),
                cash=SystemOpeningUpdate(date=date(2024, 8, 2), amount=Decimal("50.00")),
            ),
        )

        bank_tx = BankTransaction(
            date=date(2024, 8, 3),
            amount=Decimal("10.00"),
            reference="RELEVE-2",
            description="Operation courante",
            balance_after=Decimal("0"),
            source=BankTransactionSource.MANUAL,
        )
        cash_tx = CashRegister(
            date=date(2024, 8, 3),
            amount=Decimal("20.00"),
            type=CashMovementType.IN,
            reference="CAISSE-2",
            description="Recette",
            source=CashEntrySource.MANUAL,
            balance_after=Decimal("0"),
        )
        db_session.add_all([bank_tx, cash_tx])
        await db_session.flush()
        await recompute_bank_balances(db_session)
        await recompute_cash_balances(db_session)
        await db_session.commit()

        opening = await upsert_treasury_system_opening(
            db_session,
            TreasurySystemOpeningUpdate(
                bank=SystemOpeningUpdate(date=date(2024, 8, 1), amount=Decimal("80.00")),
                cash=SystemOpeningUpdate(date=date(2024, 8, 1), amount=Decimal("40.00")),
            ),
        )

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

        assert opening.bank.amount == Decimal("80.00")
        assert opening.cash.amount == Decimal("40.00")
        opening_bank_entries = [
            entry for entry in bank_entries if entry.source == BankTransactionSource.SYSTEM_OPENING
        ]
        opening_cash_entries = [
            entry for entry in cash_entries if entry.source == CashEntrySource.SYSTEM_OPENING
        ]

        assert len(opening_bank_entries) == 1
        assert len(opening_cash_entries) == 1
        assert bank_entries[0].date == date(2024, 8, 1)
        assert bank_entries[0].balance_after == Decimal("80.00")
        assert bank_entries[1].balance_after == Decimal("90.00")
        assert cash_entries[0].date == date(2024, 8, 1)
        assert cash_entries[0].balance_after == Decimal("40.00")
        assert cash_entries[1].balance_after == Decimal("60.00")
