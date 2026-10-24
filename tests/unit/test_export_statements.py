"""Unit tests for the archivable bilan / compte de résultat documents.

The template context is asserted directly rather than the rendered PDF: WeasyPrint
needs system libraries that are not available everywhere, and every figure and label
a reader cares about is already decided in the context.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.services.export_service import build_bilan_context, build_resultat_context
from backend.services.pdf_service import render_financial_statement_html


async def _account(db: AsyncSession, number: str, label: str, type_: AccountType) -> None:
    db.add(AccountingAccount(number=number, label=label, type=type_))
    await db.flush()


async def _entry(
    db: AsyncSession,
    *,
    number: str,
    account: str,
    debit: Decimal = Decimal("0"),
    credit: Decimal = Decimal("0"),
    fiscal_year_id: int,
    source_type: EntrySourceType = EntrySourceType.MANUAL,
) -> None:
    db.add(
        AccountingEntry(
            entry_number=number,
            date=date(2025, 3, 1),
            account_number=account,
            label="Écriture",
            debit=debit,
            credit=credit,
            fiscal_year_id=fiscal_year_id,
            source_type=source_type,
        )
    )
    await db.flush()


async def _closed_year(db: AsyncSession) -> FiscalYear:
    fy = FiscalYear(
        name="2025",
        start_date=date(2024, 8, 1),
        end_date=date(2025, 7, 31),
        status=FiscalYearStatus.CLOSED,
    )
    db.add(fy)
    await db.flush()
    return fy


@pytest.mark.asyncio
async def test_resultat_document_reports_a_closed_year(db_session: AsyncSession) -> None:
    """A closed year still shows its charges, produits and deficit."""
    fy = await _closed_year(db_session)
    await _account(db_session, "611100", "Sous-traitance", AccountType.CHARGE)
    await _account(db_session, "706110", "Cours", AccountType.PRODUIT)
    await _entry(
        db_session, number="1", account="611100", debit=Decimal("600"), fiscal_year_id=fy.id
    )
    await _entry(
        db_session, number="2", account="706110", credit=Decimal("400"), fiscal_year_id=fy.id
    )
    # Closing zeroes both accounts; the document must ignore it.
    await _entry(
        db_session,
        number="3",
        account="611100",
        credit=Decimal("600"),
        fiscal_year_id=fy.id,
        source_type=EntrySourceType.CLOTURE,
    )
    await _entry(
        db_session,
        number="4",
        account="706110",
        debit=Decimal("400"),
        fiscal_year_id=fy.id,
        source_type=EntrySourceType.CLOTURE,
    )

    context = await build_resultat_context(db_session, fy.id)

    assert context["title"] == "Compte de résultat"
    assert context["fiscal_year_name"] == "2025"
    assert context["sections"][0]["total"] == "600,00 €"
    assert context["sections"][1]["total"] == "400,00 €"
    assert context["result_label"] == "Déficit de l'exercice"
    assert context["result_is_negative"] is True
    assert context["show_result"] is True

    html = render_financial_statement_html(context)
    assert "Sous-traitance" in html
    assert "600,00" in html
    assert "Exercice clôturé" in html


@pytest.mark.asyncio
async def test_bilan_document_balances_with_both_sides_positive(
    db_session: AsyncSession,
) -> None:
    """Actif and passif are both shown positive, so the two totals match."""
    fy = await _closed_year(db_session)
    await _account(db_session, "512100", "Compte courant", AccountType.ACTIF)
    await _account(db_session, "106800", "Réserves", AccountType.PASSIF)
    await _entry(
        db_session, number="1", account="512100", debit=Decimal("1500"), fiscal_year_id=fy.id
    )
    await _entry(
        db_session, number="2", account="106800", credit=Decimal("1500"), fiscal_year_id=fy.id
    )

    context = await build_bilan_context(db_session, fy.id)

    actif, passif = context["sections"]
    assert actif["total"] == "1 500,00 €"
    assert passif["total"] == "1 500,00 €"
    assert passif["rows"][0]["amount"] == "1 500,00 €"
    # Nothing left in the result accounts: the standalone result line is dropped.
    assert context["show_result"] is False

    html = render_financial_statement_html(context)
    assert "Réserves" in html
    assert "Total du passif" in html
    assert "de l'exercice" not in html


@pytest.mark.asyncio
async def test_bilan_document_keeps_the_result_line_while_open(
    db_session: AsyncSession,
) -> None:
    """Before closing, the period result is not yet in the accounts and must be shown."""
    fy = FiscalYear(
        name="2026",
        start_date=date(2025, 8, 1),
        end_date=date(2026, 7, 31),
        status=FiscalYearStatus.OPEN,
    )
    db_session.add(fy)
    await db_session.flush()
    await _account(db_session, "512100", "Compte courant", AccountType.ACTIF)
    await _account(db_session, "706110", "Cours", AccountType.PRODUIT)
    await _entry(
        db_session, number="1", account="512100", debit=Decimal("800"), fiscal_year_id=fy.id
    )
    await _entry(
        db_session, number="2", account="706110", credit=Decimal("800"), fiscal_year_id=fy.id
    )

    context = await build_bilan_context(db_session, fy.id)

    assert context["show_result"] is True
    assert context["result_label"] == "Excédent de l'exercice"
    assert context["result_amount"] == "800,00 €"
    assert "Exercice en cours" in render_financial_statement_html(context)
