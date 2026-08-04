"""Unit tests for fiscal year service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import backend.services.fiscal_year_service as fiscal_year_service_module
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.schemas.fiscal_year import FiscalYearCreate
from backend.services.fiscal_year_service import (
    FiscalYearError,
    administrative_close_fiscal_year,
    close_fiscal_year,
    create_fiscal_year,
    find_fiscal_year_for_date,
    find_fiscal_year_id_for_date,
    get_current_fiscal_year,
    get_fiscal_year,
    list_fiscal_years,
    open_new_fiscal_year,
    pre_close_checks,
)


async def _create_fy(
    db: AsyncSession,
    name: str = "2024",
    start: date = date(2024, 1, 1),
    end: date = date(2024, 12, 31),
    status: FiscalYearStatus = FiscalYearStatus.OPEN,
) -> FiscalYear:
    fy = FiscalYear(name=name, start_date=start, end_date=end, status=status)
    db.add(fy)
    await db.commit()
    await db.refresh(fy)
    return fy


class TestCreateFiscalYear:
    @pytest.mark.asyncio
    async def test_creates_open_fiscal_year(self, db_session: AsyncSession) -> None:
        payload = FiscalYearCreate(
            name="2024",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        fy = await create_fiscal_year(db_session, payload)
        assert fy.id is not None
        assert fy.status == FiscalYearStatus.OPEN
        assert fy.name == "2024"

    @pytest.mark.asyncio
    async def test_rejects_a_period_overlapping_an_existing_year(
        self, db_session: AsyncSession
    ) -> None:
        """Overlapping years would make the year of an entry ambiguous."""
        await _create_fy(
            db_session, name="2024-2025", start=date(2024, 8, 1), end=date(2025, 7, 31)
        )

        payload = FiscalYearCreate(
            name="2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        with pytest.raises(FiscalYearError, match="chevauche"):
            await create_fiscal_year(db_session, payload)

    @pytest.mark.asyncio
    async def test_accepts_a_period_starting_the_day_after(self, db_session: AsyncSession) -> None:
        """Consecutive years share no day and must be accepted."""
        await _create_fy(
            db_session, name="2024-2025", start=date(2024, 8, 1), end=date(2025, 7, 31)
        )

        payload = FiscalYearCreate(
            name="2025-2026",
            start_date=date(2025, 8, 1),
            end_date=date(2026, 7, 31),
        )
        fy = await create_fiscal_year(db_session, payload)
        assert fy.start_date == date(2025, 8, 1)

    @pytest.mark.asyncio
    async def test_end_date_must_be_after_start(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            FiscalYearCreate(
                name="bad",
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1),
            )


class TestOpenNextWithSeveralBalances:
    @pytest.mark.asyncio
    async def test_carries_every_balance_with_distinct_entry_numbers(
        self, db_session: AsyncSession
    ) -> None:
        """Production failure: every RAN entry claimed the same number.

        Entry numbers were requested one at a time, and each request reads
        MAX(entry_number) from the database — which does not move until the
        flush. With a single balance sheet account nothing showed; with two the
        unique constraint blew up and the year could not be opened at all.
        """
        from backend.models.accounting_account import AccountingAccount, AccountType

        fy = await _create_fy(
            db_session, "2025", date(2025, 8, 1), date(2026, 7, 31), FiscalYearStatus.CLOSED
        )
        for number, label in (
            ("512100", "Compte courant"),
            ("530000", "Caisse"),
            ("411100", "Clients"),
        ):
            db_session.add(
                AccountingAccount(
                    number=number, label=label, type=AccountType.ACTIF, is_active=True
                )
            )
        db_session.add(
            AccountingAccount(
                number="106800", label="Réserves", type=AccountType.PASSIF, is_active=True
            )
        )
        # Counterpart so the balance sheet adds up: 2134.33 + 254.34 + 480.00.
        db_session.add(
            AccountingEntry(
                entry_number="000510",
                date=date(2026, 3, 1),
                account_number="106800",
                label="reserves",
                debit=Decimal("0"),
                credit=Decimal("2868.67"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        for index, (number, amount) in enumerate(
            (("512100", "2134.33"), ("530000", "254.34"), ("411100", "480.00"))
        ):
            db_session.add(
                AccountingEntry(
                    entry_number=f"00050{index}",
                    date=date(2026, 3, 1),
                    account_number=number,
                    label="mouvement",
                    debit=Decimal(amount),
                    credit=Decimal("0"),
                    fiscal_year_id=fy.id,
                    source_type=EntrySourceType.MANUAL,
                )
            )
        await db_session.commit()

        payload = FiscalYearCreate(
            name="2026", start_date=date(2026, 8, 1), end_date=date(2027, 7, 31)
        )
        new_fy = await open_new_fiscal_year(db_session, fy, payload)

        result = await db_session.execute(
            select(AccountingEntry).where(AccountingEntry.fiscal_year_id == new_fy.id)
        )
        ran = list(result.scalars().all())
        assert len(ran) == 4, "one carry-forward per non-zero balance sheet account"
        numbers = [entry.entry_number for entry in ran]
        assert len(set(numbers)) == 4, f"entry numbers must be distinct, got {numbers}"
        debits = {entry.account_number: entry.debit for entry in ran if entry.debit > 0}
        assert debits == {
            "512100": Decimal("2134.33"),
            "530000": Decimal("254.34"),
            "411100": Decimal("480.00"),
        }


class TestPreCloseUnbalancedGroups:
    @pytest.mark.asyncio
    async def test_names_the_offending_document(self, db_session: AsyncSession) -> None:
        """A raw total is unusable; the warning must point at the culprit."""
        fy = await _create_fy(db_session, "2025", date(2025, 8, 1), date(2026, 7, 31))
        db_session.add(
            AccountingEntry(
                entry_number="000100",
                date=date(2026, 7, 2),
                account_number="411100",
                label="Fact. 2026-0125 Piruza T.",
                debit=Decimal("80.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.INVOICE,
                source_id=2927,
                group_key="invoice:2927",
            )
        )
        db_session.add(
            AccountingEntry(
                entry_number="000101",
                date=date(2026, 7, 2),
                account_number="706110",
                label="Fact. 2026-0125 Piruza T.",
                debit=Decimal("0"),
                credit=Decimal("104.00"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.INVOICE,
                source_id=2927,
                group_key="invoice:2927",
            )
        )
        await db_session.commit()

        warnings = await pre_close_checks(db_session, fy)

        assert any("Balance déséquilibrée" in w for w in warnings)
        assert any("Fact. 2026-0125" in w and "-24.00" in w for w in warnings)


class TestPreCloseOrphanScope:
    async def _add_orphan(self, db: AsyncSession, when: date, label: str, number: str) -> None:
        db.add(
            AccountingEntry(
                entry_number=number,
                date=when,
                account_number="411100",
                label=label,
                debit=Decimal("10.00"),
                credit=Decimal("10.00"),
                fiscal_year_id=None,
            )
        )
        await db.commit()

    @pytest.mark.asyncio
    async def test_reports_only_orphans_dated_within_the_period(
        self, db_session: AsyncSession
    ) -> None:
        """Orphans outside the period cannot affect this closing — staying silent
        on them keeps the warning meaningful."""
        fy = await _create_fy(db_session, "2025", date(2025, 8, 1), date(2026, 7, 31))
        await self._add_orphan(db_session, date(2022, 11, 28), "Fact. 2022-0361", "000200")
        await self._add_orphan(db_session, date(2026, 8, 1), "Fact. 2026-0129", "000201")
        await self._add_orphan(db_session, date(2026, 3, 10), "Fact. 2026-0050", "000202")

        warnings = await pre_close_checks(db_session, fy)

        orphan_warnings = [w for w in warnings if "non rattachée" in w or "↳" in w]
        assert any("1 écriture(s)" in w for w in orphan_warnings)
        assert any("Fact. 2026-0050" in w for w in orphan_warnings)
        assert not any("2022-0361" in w for w in orphan_warnings)
        assert not any("2026-0129" in w for w in orphan_warnings)

    @pytest.mark.asyncio
    async def test_stays_silent_when_every_orphan_is_outside(
        self, db_session: AsyncSession
    ) -> None:
        fy = await _create_fy(db_session, "2025", date(2025, 8, 1), date(2026, 7, 31))
        await self._add_orphan(db_session, date(2022, 11, 28), "Fact. 2022-0361", "000200")

        warnings = await pre_close_checks(db_session, fy)

        assert warnings == []


class TestListFiscalYears:
    @pytest.mark.asyncio
    async def test_empty_list(self, db_session: AsyncSession) -> None:
        result = await list_fiscal_years(db_session)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_fiscal_years(self, db_session: AsyncSession) -> None:
        await _create_fy(db_session, "2023", date(2023, 1, 1), date(2023, 12, 31))
        await _create_fy(db_session, "2024", date(2024, 1, 1), date(2024, 12, 31))
        result = await list_fiscal_years(db_session)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_ordered_by_start_date_desc(self, db_session: AsyncSession) -> None:
        await _create_fy(db_session, "2023", date(2023, 1, 1), date(2023, 12, 31))
        await _create_fy(db_session, "2024", date(2024, 1, 1), date(2024, 12, 31))
        result = await list_fiscal_years(db_session)
        assert result[0].name == "2024"


class TestGetFiscalYear:
    @pytest.mark.asyncio
    async def test_get_existing(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session)
        found = await get_fiscal_year(db_session, fy.id)
        assert found is not None
        assert found.id == fy.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, db_session: AsyncSession) -> None:
        result = await get_fiscal_year(db_session, 999)
        assert result is None


class TestGetCurrentFiscalYear:
    @pytest.mark.asyncio
    async def test_no_open_returns_none(self, db_session: AsyncSession) -> None:
        await _create_fy(db_session, status=FiscalYearStatus.CLOSED)
        result = await get_current_fiscal_year(db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_open_year_covering_today(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2026, 4, 12)

        monkeypatch.setattr(fiscal_year_service_module, "date", _FakeDate)
        await _create_fy(
            db_session,
            "2024",
            date(2024, 8, 1),
            date(2025, 7, 31),
            FiscalYearStatus.OPEN,
        )
        fy = await _create_fy(
            db_session,
            "2025",
            date(2025, 8, 1),
            date(2026, 7, 31),
            FiscalYearStatus.OPEN,
        )
        result = await get_current_fiscal_year(db_session)
        assert result is not None
        assert result.id == fy.id

    @pytest.mark.asyncio
    async def test_returns_latest_open_when_none_covers_today(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2026, 4, 12)

        monkeypatch.setattr(fiscal_year_service_module, "date", _FakeDate)
        await _create_fy(
            db_session,
            "2023",
            date(2023, 8, 1),
            date(2024, 7, 31),
            FiscalYearStatus.OPEN,
        )
        latest_open = await _create_fy(
            db_session,
            "2024",
            date(2024, 8, 1),
            date(2025, 7, 31),
            FiscalYearStatus.OPEN,
        )

        result = await get_current_fiscal_year(db_session)

        assert result is not None
        assert result.id == latest_open.id


class TestFindFiscalYearForDate:
    @pytest.mark.asyncio
    async def test_returns_covering_fiscal_year(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session, "2025", date(2025, 1, 1), date(2025, 12, 31))

        result = await find_fiscal_year_for_date(db_session, date(2025, 8, 15))

        assert result is not None
        assert result.id == fy.id
        assert await find_fiscal_year_id_for_date(db_session, date(2025, 8, 15)) == fy.id

    @pytest.mark.asyncio
    async def test_returns_none_when_no_fiscal_year_covers_date(
        self, db_session: AsyncSession
    ) -> None:
        await _create_fy(db_session, "2024", date(2024, 1, 1), date(2024, 12, 31))

        assert await find_fiscal_year_for_date(db_session, date(2025, 1, 1)) is None
        assert await find_fiscal_year_id_for_date(db_session, date(2025, 1, 1)) is None


class TestCloseFiscalYear:
    @pytest.mark.asyncio
    async def test_close_marks_closed(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session)
        closed = await close_fiscal_year(db_session, fy)
        assert closed.status == FiscalYearStatus.CLOSED

    @pytest.mark.asyncio
    async def test_close_already_closed_raises_error(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session, status=FiscalYearStatus.CLOSED)
        with pytest.raises(FiscalYearError):
            await close_fiscal_year(db_session, fy)

    @pytest.mark.asyncio
    async def test_close_with_zero_result_no_cloture_entry(self, db_session: AsyncSession) -> None:
        """If charges == produits == 0, no CLOTURE entry should be created."""
        fy = await _create_fy(db_session)
        from sqlalchemy import select

        await close_fiscal_year(db_session, fy)
        result = await db_session.execute(
            select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.CLOTURE)
        )
        entries = result.scalars().all()
        assert entries == []

    @pytest.mark.asyncio
    async def test_close_with_nonzero_result_creates_cloture_entry(
        self, db_session: AsyncSession
    ) -> None:
        """A CLOTURE entry should be created when there is a non-zero result."""
        from backend.models.accounting_account import AccountingAccount, AccountType

        fy = await _create_fy(db_session)

        # Add a charge account and entries
        acct_charge = AccountingAccount(
            number="706110",
            label="Cours de soutien",
            type=AccountType.PRODUIT,
            is_active=True,
        )
        db_session.add(acct_charge)
        await db_session.flush()

        entry = AccountingEntry(
            entry_number="000001",
            date=date(2024, 6, 1),
            account_number="706110",
            label="Test prod",
            debit=Decimal("0"),
            credit=Decimal("500.00"),
            fiscal_year_id=fy.id,
            source_type=EntrySourceType.INVOICE,
            source_id=1,
        )
        db_session.add(entry)
        await db_session.commit()

        from sqlalchemy import select

        await close_fiscal_year(db_session, fy)
        result = await db_session.execute(
            select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.CLOTURE)
        )
        cloture_entries = result.scalars().all()
        assert len(cloture_entries) >= 1
        assert cloture_entries[0].fiscal_year_id == fy.id


class TestClosingEntryShape:
    """The closing entry is what makes the next year's opening balance right."""

    async def _year_with_activity(
        self, db: AsyncSession, *, produits: str, charges: str
    ) -> FiscalYear:
        from backend.models.accounting_account import AccountingAccount, AccountType

        fy = await _create_fy(db, "2025", date(2025, 8, 1), date(2026, 7, 31))
        db.add_all(
            [
                AccountingAccount(
                    number="706110", label="Cours", type=AccountType.PRODUIT, is_active=True
                ),
                AccountingAccount(
                    number="641000", label="Salaires", type=AccountType.CHARGE, is_active=True
                ),
                AccountingAccount(
                    number="512100", label="Banque", type=AccountType.ACTIF, is_active=True
                ),
                # The result accounts must be part of the chart, otherwise the
                # carry-forward silently skips them.
                AccountingAccount(
                    number="120000", label="Excédent", type=AccountType.PASSIF, is_active=True
                ),
                AccountingAccount(
                    number="129000", label="Déficit", type=AccountType.PASSIF, is_active=True
                ),
            ]
        )
        # Revenue collected in the bank, wages paid from it: a self-contained year.
        db.add_all(
            [
                AccountingEntry(
                    entry_number="000010",
                    date=date(2026, 1, 5),
                    account_number="706110",
                    label="produits",
                    debit=Decimal("0"),
                    credit=Decimal(produits),
                    fiscal_year_id=fy.id,
                    source_type=EntrySourceType.INVOICE,
                ),
                AccountingEntry(
                    entry_number="000011",
                    date=date(2026, 1, 5),
                    account_number="512100",
                    label="encaissement",
                    debit=Decimal(produits),
                    credit=Decimal("0"),
                    fiscal_year_id=fy.id,
                    source_type=EntrySourceType.INVOICE,
                ),
                AccountingEntry(
                    entry_number="000012",
                    date=date(2026, 2, 5),
                    account_number="641000",
                    label="charges",
                    debit=Decimal(charges),
                    credit=Decimal("0"),
                    fiscal_year_id=fy.id,
                    source_type=EntrySourceType.SALARY,
                ),
                AccountingEntry(
                    entry_number="000013",
                    date=date(2026, 2, 5),
                    account_number="512100",
                    label="paiement",
                    debit=Decimal("0"),
                    credit=Decimal(charges),
                    fiscal_year_id=fy.id,
                    source_type=EntrySourceType.SALARY,
                ),
            ]
        )
        await db.commit()
        return fy

    async def _closing_entries(self, db: AsyncSession, fy: FiscalYear) -> list[AccountingEntry]:
        result = await db.execute(
            select(AccountingEntry).where(
                AccountingEntry.source_type == EntrySourceType.CLOTURE,
                AccountingEntry.fiscal_year_id == fy.id,
            )
        )
        return list(result.scalars().all())

    @pytest.mark.asyncio
    async def test_closing_entry_is_balanced(self, db_session: AsyncSession) -> None:
        """It used to post a single line with no counterpart, unbalancing the year."""
        fy = await self._year_with_activity(db_session, produits="1000.00", charges="600.00")

        await close_fiscal_year(db_session, fy)

        entries = await self._closing_entries(db_session, fy)
        assert sum(e.debit for e in entries) == sum(e.credit for e in entries)
        assert len({e.entry_number for e in entries}) == len(entries)

    @pytest.mark.asyncio
    async def test_result_accounts_are_cleared(self, db_session: AsyncSession) -> None:
        """Leaving them loaded is what made the carry-forward lopsided."""
        fy = await self._year_with_activity(db_session, produits="1000.00", charges="600.00")

        await close_fiscal_year(db_session, fy)

        for account in ("706110", "641000"):
            result = await db_session.execute(
                select(func.sum(AccountingEntry.debit) - func.sum(AccountingEntry.credit)).where(
                    AccountingEntry.fiscal_year_id == fy.id,
                    AccountingEntry.account_number == account,
                )
            )
            assert Decimal(str(result.scalar_one())) == Decimal("0"), account

    @pytest.mark.asyncio
    async def test_surplus_is_credited_to_120000(self, db_session: AsyncSession) -> None:
        fy = await self._year_with_activity(db_session, produits="1000.00", charges="600.00")

        await close_fiscal_year(db_session, fy)

        entry = next(
            e for e in await self._closing_entries(db_session, fy) if e.account_number == "120000"
        )
        assert entry.credit == Decimal("400.00")
        assert entry.debit == Decimal("0")

    @pytest.mark.asyncio
    async def test_deficit_is_debited_to_129000(self, db_session: AsyncSession) -> None:
        fy = await self._year_with_activity(db_session, produits="600.00", charges="1000.00")

        await close_fiscal_year(db_session, fy)

        entry = next(
            e for e in await self._closing_entries(db_session, fy) if e.account_number == "129000"
        )
        assert entry.debit == Decimal("400.00")
        assert entry.credit == Decimal("0")

    @pytest.mark.asyncio
    async def test_next_year_opens_on_a_balanced_carry_forward(
        self, db_session: AsyncSession
    ) -> None:
        """The end-to-end check: close, then open, and the new year must balance.

        This is what failed in production — the carry-forward faithfully copied a
        balance sheet that did not add up, because the result accounts had never
        been cleared.
        """
        fy = await self._year_with_activity(db_session, produits="1000.00", charges="600.00")
        await close_fiscal_year(db_session, fy)

        new_fy = await open_new_fiscal_year(
            db_session,
            fy,
            FiscalYearCreate(name="2026", start_date=date(2026, 8, 1), end_date=date(2027, 7, 31)),
        )

        result = await db_session.execute(
            select(AccountingEntry).where(AccountingEntry.fiscal_year_id == new_fy.id)
        )
        ran = list(result.scalars().all())
        assert ran, "the new year must carry something forward"
        assert sum(e.debit for e in ran) == sum(e.credit for e in ran)


class TestCarryForwardGuard:
    @pytest.mark.asyncio
    async def test_refuses_to_open_on_an_unbalanced_carry_forward(
        self, db_session: AsyncSession
    ) -> None:
        """Production case: a year closed without clearing its result accounts.

        The carry-forward faithfully copied a balance sheet that did not add up,
        and the new year opened lopsided. Refusing is the only sane answer — the
        whole year would be built on it.
        """
        from backend.models.accounting_account import AccountingAccount, AccountType

        fy = await _create_fy(
            db_session, "2025", date(2025, 8, 1), date(2026, 7, 31), FiscalYearStatus.CLOSED
        )
        db_session.add(
            AccountingAccount(
                number="512100", label="Banque", type=AccountType.ACTIF, is_active=True
            )
        )
        # A lone debit on a balance sheet account: nothing balances it.
        db_session.add(
            AccountingEntry(
                entry_number="000020",
                date=date(2026, 1, 5),
                account_number="512100",
                label="solde orphelin",
                debit=Decimal("400.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        with pytest.raises(FiscalYearError, match="Report à nouveau déséquilibré"):
            await open_new_fiscal_year(
                db_session,
                fy,
                FiscalYearCreate(
                    name="2026", start_date=date(2026, 8, 1), end_date=date(2027, 7, 31)
                ),
            )


class TestAdministrativeCloseFiscalYear:
    @pytest.mark.asyncio
    async def test_marks_closed_without_creating_cloture_entries(
        self, db_session: AsyncSession
    ) -> None:
        fy = await _create_fy(db_session)

        closed = await administrative_close_fiscal_year(db_session, fy)

        assert closed.status == FiscalYearStatus.CLOSED

        from sqlalchemy import select

        result = await db_session.execute(
            select(AccountingEntry).where(AccountingEntry.source_type == EntrySourceType.CLOTURE)
        )
        assert result.scalars().all() == []

    @pytest.mark.asyncio
    async def test_already_closed_raises_error(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session, status=FiscalYearStatus.CLOSED)

        with pytest.raises(FiscalYearError):
            await administrative_close_fiscal_year(db_session, fy)


class TestPreCloseChecks:
    @pytest.mark.asyncio
    async def test_returns_empty_for_balanced_open_fy(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session)
        # Balanced entry pair
        db_session.add(
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 6, 1),
                account_number="512000",
                label="Debit",
                debit=Decimal("100.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        db_session.add(
            AccountingEntry(
                entry_number="000002",
                date=date(2024, 6, 1),
                account_number="411000",
                label="Credit",
                debit=Decimal("0"),
                credit=Decimal("100.00"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        warnings = await pre_close_checks(db_session, fy)
        assert warnings == []

    @pytest.mark.asyncio
    async def test_warns_on_unbalanced_entries(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session)
        db_session.add(
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 6, 1),
                account_number="512000",
                label="Debit only",
                debit=Decimal("200.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        warnings = await pre_close_checks(db_session, fy)
        assert any("déséquilibrée" in w.lower() or "Balance" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_warns_on_orphan_entries(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session)
        db_session.add(
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 6, 1),
                account_number="512000",
                label="Orphan",
                debit=Decimal("100.00"),
                credit=Decimal("0"),
                fiscal_year_id=None,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        warnings = await pre_close_checks(db_session, fy)
        # Dated inside the period, so still reported — with the wording that now
        # says what it means for the closing.
        assert any("non rattachée" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_returns_warning_if_fy_not_open(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session, status=FiscalYearStatus.CLOSED)
        warnings = await pre_close_checks(db_session, fy)
        assert len(warnings) == 1
        assert "pas ouvert" in warnings[0]


class TestOpenNewFiscalYear:
    @pytest.mark.asyncio
    async def test_requires_closed_source_fy(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session)
        payload = FiscalYearCreate(
            name="2025", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        with pytest.raises(FiscalYearError, match="CLOSED"):
            await open_new_fiscal_year(db_session, fy, payload)

    @pytest.mark.asyncio
    async def test_creates_new_fy_with_ran_entries(self, db_session: AsyncSession) -> None:
        from sqlalchemy import select

        from backend.models.accounting_account import AccountingAccount, AccountType

        fy = await _create_fy(db_session, status=FiscalYearStatus.CLOSED)

        # Create an actif account
        acct = AccountingAccount(
            number="512000", label="Banque", type=AccountType.ACTIF, is_active=True
        )
        # A balance sheet only carries forward if it balances: give the bank
        # position its counterpart in equity.
        db_session.add(
            AccountingAccount(
                number="106800", label="Réserves", type=AccountType.PASSIF, is_active=True
            )
        )
        db_session.add(
            AccountingEntry(
                entry_number="000003",
                date=date(2024, 6, 1),
                account_number="106800",
                label="reserves",
                debit=Decimal("0"),
                credit=Decimal("700.00"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        db_session.add(acct)
        await db_session.flush()

        # Add entries in the closed FY with a net debit balance
        db_session.add(
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 3, 1),
                account_number="512000",
                label="Deposit",
                debit=Decimal("1000.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        db_session.add(
            AccountingEntry(
                entry_number="000002",
                date=date(2024, 6, 1),
                account_number="512000",
                label="Withdrawal",
                debit=Decimal("0"),
                credit=Decimal("300.00"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        payload = FiscalYearCreate(
            name="2025", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        new_fy = await open_new_fiscal_year(db_session, fy, payload)

        assert new_fy.status == FiscalYearStatus.OPEN
        assert new_fy.name == "2025"

        # Check RAN entry was created for the new FY
        result = await db_session.execute(
            select(AccountingEntry).where(
                AccountingEntry.fiscal_year_id == new_fy.id,
                AccountingEntry.source_type == EntrySourceType.CLOTURE,
            )
        )
        ran_entries = list(result.scalars().all())
        # Bank position and its equity counterpart.
        assert len(ran_entries) == 2
        bank = next(entry for entry in ran_entries if entry.account_number == "512000")
        assert bank.debit == Decimal("700.00")  # 1000 - 300
        assert bank.credit == Decimal("0")
        assert sum(e.debit for e in ran_entries) == sum(e.credit for e in ran_entries)

    @pytest.mark.asyncio
    async def test_no_ran_for_zero_balance_accounts(self, db_session: AsyncSession) -> None:
        from sqlalchemy import select

        from backend.models.accounting_account import AccountingAccount, AccountType

        fy = await _create_fy(db_session, status=FiscalYearStatus.CLOSED)

        acct = AccountingAccount(
            number="512000", label="Banque", type=AccountType.ACTIF, is_active=True
        )
        db_session.add(acct)
        # Balanced entries → zero balance
        db_session.add(
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 3, 1),
                account_number="512000",
                label="In",
                debit=Decimal("500.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        db_session.add(
            AccountingEntry(
                entry_number="000002",
                date=date(2024, 6, 1),
                account_number="512000",
                label="Out",
                debit=Decimal("0"),
                credit=Decimal("500.00"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        payload = FiscalYearCreate(
            name="2025", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        new_fy = await open_new_fiscal_year(db_session, fy, payload)

        result = await db_session.execute(
            select(AccountingEntry).where(AccountingEntry.fiscal_year_id == new_fy.id)
        )
        assert result.scalars().all() == []
