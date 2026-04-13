"""Unit tests for fiscal year service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
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
    async def test_end_date_must_be_after_start(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            FiscalYearCreate(
                name="bad",
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1),
            )


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
