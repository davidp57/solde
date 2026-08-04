"""Export service — CSV and PDF exports for accounting reports."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def _write_csv(headers: list[str], rows: list[list[Any]]) -> bytes:
    """Serialize rows to CSV bytes (UTF-8 with BOM for Excel compat)."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    writer.writerows(rows)
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


async def export_journal_csv(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    account_number: str | None = None,
    fiscal_year_id: int | None = None,
) -> bytes:
    """Export journal entries to CSV."""
    from backend.services.accounting_entry_service import get_journal  # noqa: PLC0415

    entries = await get_journal(
        db,
        from_date=from_date,
        to_date=to_date,
        account_number=account_number,
        fiscal_year_id=fiscal_year_id,
        limit=None,
    )

    headers = ["N° pièce", "Date", "Compte", "Libellé", "Débit", "Crédit", "Source"]
    rows = [
        [
            e.entry_number,
            e.date.strftime("%d/%m/%Y"),
            e.account_number,
            e.label,
            f"{e.debit:.2f}".replace(".", ","),
            f"{e.credit:.2f}".replace(".", ","),
            e.source_type or "",
        ]
        for e in entries
    ]
    return _write_csv(headers, rows)


async def export_balance_csv(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    fiscal_year_id: int | None = None,
) -> bytes:
    """Export balance to CSV."""
    from backend.services.accounting_entry_service import get_balance  # noqa: PLC0415

    rows_data = await get_balance(
        db, from_date=from_date, to_date=to_date, fiscal_year_id=fiscal_year_id
    )

    headers = ["Compte", "Libellé", "Type", "Débit", "Crédit", "Solde"]
    rows = [
        [
            r.account_number,
            r.account_label,
            r.account_type,
            f"{r.total_debit:.2f}".replace(".", ","),
            f"{r.total_credit:.2f}".replace(".", ","),
            f"{r.solde:.2f}".replace(".", ","),
        ]
        for r in rows_data
    ]
    return _write_csv(headers, rows)


async def export_resultat_csv(db: AsyncSession, fiscal_year_id: int | None = None) -> bytes:
    """Export compte de résultat to CSV."""
    from backend.services.accounting_entry_service import get_resultat  # noqa: PLC0415

    data = await get_resultat(db, fiscal_year_id=fiscal_year_id)

    headers = ["Section", "Compte", "Libellé", "Montant"]
    rows: list[list[Any]] = []
    for r in data.charges:
        rows.append(
            [
                "Charges",
                r.account_number,
                r.account_label,
                f"{r.solde:.2f}".replace(".", ","),
            ]
        )
    rows.append(["TOTAL CHARGES", "", "", f"{data.total_charges:.2f}".replace(".", ",")])
    for r in data.produits:
        rows.append(
            [
                "Produits",
                r.account_number,
                r.account_label,
                f"{r.solde:.2f}".replace(".", ","),
            ]
        )
    rows.append(["TOTAL PRODUITS", "", "", f"{data.total_produits:.2f}".replace(".", ",")])
    rows.append(["RÉSULTAT", "", "", f"{data.resultat:.2f}".replace(".", ",")])
    return _write_csv(headers, rows)


async def export_bilan_csv(db: AsyncSession, fiscal_year_id: int | None = None) -> bytes:
    """Export simplified bilan to CSV."""
    from backend.services.accounting_entry_service import get_bilan  # noqa: PLC0415

    data = await get_bilan(db, fiscal_year_id=fiscal_year_id)

    headers = ["Section", "Compte", "Libellé", "Solde"]
    rows: list[list[Any]] = []
    for r in data.actif:
        rows.append(
            [
                "Actif",
                r.account_number,
                r.account_label,
                f"{r.solde:.2f}".replace(".", ","),
            ]
        )
    rows.append(["TOTAL ACTIF", "", "", f"{data.total_actif:.2f}".replace(".", ",")])
    for r in data.passif:
        rows.append(
            [
                "Passif",
                r.account_number,
                r.account_label,
                f"{r.solde:.2f}".replace(".", ","),
            ]
        )
    rows.append(["Résultat de l'exercice", "", "", f"{data.resultat:.2f}".replace(".", ",")])
    rows.append(["TOTAL PASSIF", "", "", f"{data.total_passif:.2f}".replace(".", ",")])
    return _write_csv(headers, rows)


# ---------------------------------------------------------------------------
# PDF exports — bilan and compte de résultat, for archiving
# ---------------------------------------------------------------------------


def _fmt_amount(value: Decimal) -> str:
    """Format a Decimal the French way: thousands spaced, comma decimal, € suffix."""
    formatted = f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} €"


async def _statement_context(db: AsyncSession, fiscal_year_id: int | None) -> dict[str, Any]:
    """Build the header context shared by both statements."""
    from backend.services.settings import get_settings  # noqa: PLC0415

    settings = await get_settings(db)
    name: str | None = None
    status: str | None = None
    period: str | None = None
    if fiscal_year_id is not None:
        from backend.models.fiscal_year import FiscalYear  # noqa: PLC0415

        fy = await db.get(FiscalYear, fiscal_year_id)
        if fy is not None:
            name = fy.name
            status = str(fy.status)
            period = f"Du {fy.start_date:%d/%m/%Y} au {fy.end_date:%d/%m/%Y}"
    return {
        "settings": settings,
        "fiscal_year_name": name,
        "fiscal_year_status": status,
        "period": period,
        "generated_at": f"{date.today():%d/%m/%Y}",
    }


def _statement_rows(rows: Iterable[Any]) -> list[dict[str, str]]:
    """Flatten balance rows into template-ready dicts."""
    return [
        {
            "account_number": r.account_number,
            "account_label": r.account_label,
            "amount": _fmt_amount(r.solde),
        }
        for r in rows
    ]


def _render_statement_pdf(context: dict[str, Any]) -> bytes:
    """Render the shared financial-statement template to PDF bytes.

    WeasyPrint is imported lazily to keep it out of the startup memory budget.
    """
    from weasyprint import HTML  # noqa: PLC0415

    from backend.services.pdf_service import render_financial_statement_html  # noqa: PLC0415

    return bytes(HTML(string=render_financial_statement_html(context)).write_pdf())


async def build_resultat_context(
    db: AsyncSession, fiscal_year_id: int | None = None
) -> dict[str, Any]:
    """Assemble the compte de résultat template context (rendering-free, so testable)."""
    from backend.services.accounting_entry_service import get_resultat  # noqa: PLC0415

    data = await get_resultat(db, fiscal_year_id=fiscal_year_id)
    context = await _statement_context(db, fiscal_year_id)
    deficit = data.resultat < 0
    context.update(
        title="Compte de résultat",
        sections=[
            {
                "title": "Charges",
                "amount_header": "Montant",
                "rows": _statement_rows(data.charges),
                "total_label": "Total des charges",
                "total": _fmt_amount(data.total_charges),
            },
            {
                "title": "Produits",
                "amount_header": "Montant",
                "rows": _statement_rows(data.produits),
                "total_label": "Total des produits",
                "total": _fmt_amount(data.total_produits),
            },
        ],
        result_label="Déficit de l'exercice" if deficit else "Excédent de l'exercice",
        result_amount=_fmt_amount(data.resultat),
        result_is_negative=deficit,
        show_result=True,
    )
    return context


async def export_resultat_pdf(db: AsyncSession, fiscal_year_id: int | None = None) -> bytes:
    """Export the compte de résultat as an archivable PDF."""
    return _render_statement_pdf(await build_resultat_context(db, fiscal_year_id))


async def build_bilan_context(
    db: AsyncSession, fiscal_year_id: int | None = None
) -> dict[str, Any]:
    """Assemble the bilan template context (rendering-free, so testable)."""
    from backend.services.accounting_entry_service import get_bilan  # noqa: PLC0415

    data = await get_bilan(db, fiscal_year_id=fiscal_year_id)
    context = await _statement_context(db, fiscal_year_id)
    deficit = data.resultat < 0
    context.update(
        title="Bilan",
        sections=[
            {
                "title": "Actif",
                "amount_header": "Solde",
                "rows": _statement_rows(data.actif),
                "total_label": "Total de l'actif",
                "total": _fmt_amount(data.total_actif),
            },
            {
                "title": "Passif",
                "amount_header": "Solde",
                "rows": _statement_rows(data.passif),
                "total_label": "Total du passif",
                "total": _fmt_amount(data.total_passif),
            },
        ],
        result_label="Déficit de l'exercice" if deficit else "Excédent de l'exercice",
        result_amount=_fmt_amount(data.resultat),
        result_is_negative=deficit,
        # Once the year is closed the result already sits in 120000/129000 among the
        # passif accounts; repeating it as a nil line would only puzzle the reader.
        show_result=data.resultat != 0,
    )
    return context


async def export_bilan_pdf(db: AsyncSession, fiscal_year_id: int | None = None) -> bytes:
    """Export the simplified bilan as an archivable PDF."""
    return _render_statement_pdf(await build_bilan_context(db, fiscal_year_id))
