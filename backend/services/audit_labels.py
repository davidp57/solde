"""Human-readable labels for audit targets.

An audit entry names its target as ``(target_type, target_id)``, which tells an
administrator nothing ("bank_transaction #447") and dies with the target. This
module turns the pair into a short French label — "15/03/2026 · 150,00 € · VIR
DUPONT" — that :func:`backend.services.audit_service.record_audit` stores with the
entry. Labels are built in bulk, one query per target type, so labelling a page of
entries or a whole bulk reconciliation stays cheap.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable, Iterable
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank import BankTransaction, Deposit
from backend.models.cash import CashCount, CashRegister
from backend.models.checklist import ChecklistSession
from backend.models.contact import Contact
from backend.models.document import Document
from backend.models.import_run import ImportRun
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.models.salary import Salary
from backend.models.user import User

#: Labels longer than this are cut: a label identifies, the target holds the rest.
MAX_LABEL_LENGTH = 160

_SEPARATOR = " · "

TargetKey = tuple[str, int]
_Builder = Callable[[AsyncSession, set[int]], Awaitable[dict[int, str]]]


def _fmt_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def _fmt_amount(value: Decimal | None) -> str:
    if value is None:
        return ""
    text = f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return f"{text} €"


def _join(*parts: str | None) -> str:
    label = _SEPARATOR.join(p.strip() for p in parts if p and p.strip())
    if len(label) > MAX_LABEL_LENGTH:
        return label[: MAX_LABEL_LENGTH - 1].rstrip() + "…"
    return label


def _name(prenom: str | None, nom: str | None) -> str:
    return " ".join(p for p in (prenom, nom) if p)


# Every builder selects plain columns, never ORM entities: the label is computed in the
# middle of a request whose objects are already loaded, and selecting an entity hands
# back those same instances — under SQLAlchemy 2.1 that disturbed relationships the
# request was about to serialise (MissingGreenlet on Invoice.lines).


async def _bank_transactions(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    rows = await db.execute(
        select(
            BankTransaction.id,
            BankTransaction.date,
            BankTransaction.amount,
            BankTransaction.description,
        ).where(BankTransaction.id.in_(ids))
    )
    return {
        tx_id: _join(_fmt_date(day), _fmt_amount(amount), description)
        for tx_id, day, amount, description in rows.tuples()
    }


async def _invoices(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    rows = await db.execute(
        select(Invoice.id, Invoice.number, Contact.prenom, Contact.nom)
        .outerjoin(Contact, Contact.id == Invoice.contact_id)
        .where(Invoice.id.in_(ids))
    )
    return {
        invoice_id: _join(number, _name(prenom, nom))
        for invoice_id, number, prenom, nom in rows.tuples()
    }


async def _payments(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    rows = await db.execute(
        select(Payment.id, Payment.date, Payment.amount, Invoice.number)
        .outerjoin(Invoice, Invoice.id == Payment.invoice_id)
        .where(Payment.id.in_(ids))
    )
    return {
        payment_id: _join(_fmt_date(day), _fmt_amount(amount), number)
        for payment_id, day, amount, number in rows.tuples()
    }


async def _contacts(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    rows = await db.execute(
        select(Contact.id, Contact.prenom, Contact.nom).where(Contact.id.in_(ids))
    )
    return {contact_id: _join(_name(prenom, nom)) for contact_id, prenom, nom in rows.tuples()}


async def _cash_entries(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    rows = await db.execute(
        select(
            CashRegister.id, CashRegister.date, CashRegister.amount, CashRegister.description
        ).where(CashRegister.id.in_(ids))
    )
    return {
        entry_id: _join(_fmt_date(day), _fmt_amount(amount), description)
        for entry_id, day, amount, description in rows.tuples()
    }


async def _cash_counts(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    rows = await db.execute(
        select(CashCount.id, CashCount.date, CashCount.total_counted).where(CashCount.id.in_(ids))
    )
    return {
        count_id: _join(_fmt_date(day), _fmt_amount(total))
        for count_id, day, total in rows.tuples()
    }


async def _salaries(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    rows = await db.execute(
        select(Salary.id, Salary.month, Contact.prenom, Contact.nom)
        .outerjoin(Contact, Contact.id == Salary.employee_id)
        .where(Salary.id.in_(ids))
    )
    return {
        salary_id: _join(month, _name(prenom, nom))
        for salary_id, month, prenom, nom in rows.tuples()
    }


async def _deposits(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    rows = await db.execute(
        select(Deposit.id, Deposit.date, Deposit.total_amount).where(Deposit.id.in_(ids))
    )
    return {
        deposit_id: _join(f"Bordereau #{deposit_id}", _fmt_date(day), _fmt_amount(total))
        for deposit_id, day, total in rows.tuples()
    }


async def _single_column(
    db: AsyncSession, id_column: Any, label_column: Any, ids: set[int]
) -> dict[int, str]:
    rows = await db.execute(select(id_column, label_column).where(id_column.in_(ids)))
    return {target_id: _join(label) for target_id, label in rows.tuples()}


async def _documents(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    return await _single_column(db, Document.id, Document.title, ids)


async def _users(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    return await _single_column(db, User.id, User.username, ids)


async def _import_runs(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    return await _single_column(db, ImportRun.id, ImportRun.file_name, ids)


async def _checklist_sessions(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    return await _single_column(db, ChecklistSession.id, ChecklistSession.period, ids)


_BUILDERS: dict[str, _Builder] = {
    "bank_transaction": _bank_transactions,
    "bank_deposit": _deposits,
    "invoice": _invoices,
    "payment": _payments,
    "contact": _contacts,
    "cash_entry": _cash_entries,
    "cash_count": _cash_counts,
    "salary": _salaries,
    "document": _documents,
    "user": _users,
    "import_run": _import_runs,
    "checklist_session": _checklist_sessions,
}


async def describe_targets(db: AsyncSession, targets: Iterable[TargetKey]) -> dict[TargetKey, str]:
    """Return a label for each target that still exists, one query per target type.

    Missing targets and unknown types are absent from the result.
    """
    ids_by_type: dict[str, set[int]] = defaultdict(set)
    for target_type, target_id in targets:
        if target_type in _BUILDERS:
            ids_by_type[target_type].add(target_id)
    labels: dict[TargetKey, str] = {}
    for target_type, ids in ids_by_type.items():
        for target_id, label in (await _BUILDERS[target_type](db, ids)).items():
            if label:
                labels[(target_type, target_id)] = label
    return labels


async def describe_target(db: AsyncSession, target_type: str, target_id: int) -> str | None:
    """Return the label of one target, or None if it no longer exists."""
    labels = await describe_targets(db, [(target_type, target_id)])
    return labels.get((target_type, target_id))
