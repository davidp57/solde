"""Application settings service — read and update the single settings row."""

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import Base
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.app_settings import AppSettings
from backend.models.bank import (
    BankTransaction,
    BankTransactionSource,
    Deposit,
    bank_transaction_payments,
    deposit_payments,
)
from backend.models.cash import (
    CASH_SYSTEM_OPENING_DESCRIPTION,
    CashEntrySource,
    CashMovementType,
    CashRegister,
)
from backend.models.contact import Contact
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.import_log import ImportLog, ImportLogStatus, ImportLogType
from backend.models.import_run import ImportRun
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.models.salary import Salary
from backend.schemas.settings import (
    AppSettingsUpdate,
    SelectiveResetPreviewRead,
    SelectiveResetRequest,
    SystemOpeningRead,
    TreasurySystemOpeningRead,
    TreasurySystemOpeningUpdate,
)

logger = logging.getLogger(__name__)

_SETTINGS_ID = 1
_PRESERVED_TABLES = {"users"}
_IMPORT_FILE_YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")
_SELECTIVE_RESET_OBJECT_TYPES = (
    "contact",
    "invoice",
    "payment",
    "salary",
    "cash_register",
    "bank_transaction",
    "accounting_entry",
    "deposit",
)
_ROOT_OBJECT_TYPES = tuple(
    object_type for object_type in _SELECTIVE_RESET_OBJECT_TYPES if object_type != "deposit"
)


@dataclass
class _SelectiveResetPlan:
    import_type: ImportLogType
    fiscal_year: FiscalYear
    import_log_ids: set[int] = field(default_factory=set)
    import_run_ids: set[int] = field(default_factory=set)
    root_object_ids: dict[str, set[int]] = field(
        default_factory=lambda: {object_type: set() for object_type in _ROOT_OBJECT_TYPES}
    )
    derived_object_ids: dict[str, set[int]] = field(
        default_factory=lambda: {
            object_type: set() for object_type in _SELECTIVE_RESET_OBJECT_TYPES
        }
    )
    delete_object_ids: dict[str, set[int]] = field(
        default_factory=lambda: {
            object_type: set() for object_type in _SELECTIVE_RESET_OBJECT_TYPES
        }
    )
    unlink_bank_transaction_ids: set[int] = field(default_factory=set)

    def to_preview(self) -> SelectiveResetPreviewRead:
        return SelectiveResetPreviewRead(
            import_type=self.import_type,
            fiscal_year_id=self.fiscal_year.id,
            fiscal_year_name=self.fiscal_year.name,
            fiscal_year_start_date=self.fiscal_year.start_date,
            fiscal_year_end_date=self.fiscal_year.end_date,
            matched_import_logs=len(self.import_log_ids),
            matched_import_runs=len(self.import_run_ids),
            root_objects={
                object_type: len(self.root_object_ids[object_type])
                for object_type in _ROOT_OBJECT_TYPES
                if self.root_object_ids[object_type]
            },
            derived_objects={
                object_type: len(self.derived_object_ids[object_type])
                for object_type in _SELECTIVE_RESET_OBJECT_TYPES
                if self.derived_object_ids[object_type]
            },
            delete_plan={
                **{
                    object_type: len(self.delete_object_ids[object_type])
                    for object_type in _SELECTIVE_RESET_OBJECT_TYPES
                    if self.delete_object_ids[object_type]
                },
                **({"import_logs": len(self.import_log_ids)} if self.import_log_ids else {}),
                **({"import_runs": len(self.import_run_ids)} if self.import_run_ids else {}),
            },
        )


def _deserialize_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _file_matches_fiscal_year(file_name: str | None, fiscal_year: FiscalYear) -> bool:
    if not file_name:
        return False
    return _IMPORT_FILE_YEAR_RE.search(file_name) is not None and fiscal_year.name in file_name


async def _get_fiscal_year_or_raise(db: AsyncSession, fiscal_year_id: int) -> FiscalYear:
    fiscal_year = await db.get(FiscalYear, fiscal_year_id)
    if fiscal_year is None:
        raise LookupError("Fiscal year not found")
    return fiscal_year


def _merge_created_objects(summary: dict[str, Any], target: dict[str, set[int]]) -> None:
    created_objects = summary.get("created_objects", [])
    if not isinstance(created_objects, list):
        return
    for item in created_objects:
        if not isinstance(item, dict):
            continue
        object_type = item.get("object_type")
        object_id = item.get("object_id")
        if object_type not in target or not isinstance(object_id, int):
            continue
        target[object_type].add(object_id)


async def _filter_existing_ids(
    db: AsyncSession,
    model: type[Any],
    ids: set[int],
) -> set[int]:
    if not ids:
        return set()
    result = await db.execute(select(model.id).where(model.id.in_(ids)))
    return set(result.scalars().all())


async def _refresh_existing_root_objects(db: AsyncSession, object_ids: dict[str, set[int]]) -> None:
    model_by_type: dict[str, type[Any]] = {
        "contact": Contact,
        "invoice": Invoice,
        "payment": Payment,
        "salary": Salary,
        "cash_register": CashRegister,
        "bank_transaction": BankTransaction,
        "accounting_entry": AccountingEntry,
    }
    for object_type, model in model_by_type.items():
        object_ids[object_type] = await _filter_existing_ids(db, model, object_ids[object_type])


async def _collect_import_scope_plan(
    db: AsyncSession,
    payload: SelectiveResetRequest,
) -> _SelectiveResetPlan:
    fiscal_year = await _get_fiscal_year_or_raise(db, payload.fiscal_year_id)
    plan = _SelectiveResetPlan(import_type=payload.import_type, fiscal_year=fiscal_year)

    import_logs = (
        (
            await db.execute(
                select(ImportLog).where(
                    ImportLog.import_type == payload.import_type,
                    ImportLog.status == ImportLogStatus.SUCCESS,
                )
            )
        )
        .scalars()
        .all()
    )
    for import_log in import_logs:
        if not _file_matches_fiscal_year(import_log.file_name, fiscal_year):
            continue
        plan.import_log_ids.add(import_log.id)
        _merge_created_objects(_deserialize_json(import_log.summary), plan.root_object_ids)

    import_runs = (
        (await db.execute(select(ImportRun).where(ImportRun.import_type == payload.import_type)))
        .scalars()
        .all()
    )
    for import_run in import_runs:
        if not _file_matches_fiscal_year(import_run.file_name, fiscal_year):
            continue
        summary = _deserialize_json(import_run.summary_json)
        if not summary.get("created_objects"):
            continue
        plan.import_run_ids.add(import_run.id)
        _merge_created_objects(summary, plan.root_object_ids)

    await _refresh_existing_root_objects(db, plan.root_object_ids)
    for object_type in _ROOT_OBJECT_TYPES:
        plan.delete_object_ids[object_type].update(plan.root_object_ids[object_type])

    return plan


async def _derive_invoice_payments(db: AsyncSession, invoice_ids: set[int]) -> set[int]:
    if not invoice_ids:
        return set()
    result = await db.execute(select(Payment.id).where(Payment.invoice_id.in_(invoice_ids)))
    return set(result.scalars().all())


async def _derive_transaction_payments(
    db: AsyncSession,
    bank_transaction_ids: set[int],
) -> set[int]:
    if not bank_transaction_ids:
        return set()
    result = await db.execute(
        select(bank_transaction_payments.c.payment_id).where(
            bank_transaction_payments.c.transaction_id.in_(bank_transaction_ids)
        )
    )
    linked_ids = set(result.scalars().all())
    legacy_result = await db.execute(
        select(BankTransaction.payment_id).where(BankTransaction.id.in_(bank_transaction_ids))
    )
    linked_ids.update(payment_id for payment_id in legacy_result.scalars().all() if payment_id)
    return linked_ids


async def _derive_payment_deposits(db: AsyncSession, payment_ids: set[int]) -> set[int]:
    if not payment_ids:
        return set()
    result = await db.execute(
        select(deposit_payments.c.deposit_id).where(deposit_payments.c.payment_id.in_(payment_ids))
    )
    return set(result.scalars().all())


async def _derive_payment_cash_entries(db: AsyncSession, payment_ids: set[int]) -> set[int]:
    if not payment_ids:
        return set()
    result = await db.execute(
        select(CashRegister.id).where(CashRegister.payment_id.in_(payment_ids))
    )
    return set(result.scalars().all())


async def _derive_deposit_cash_entries(db: AsyncSession, deposit_ids: set[int]) -> set[int]:
    if not deposit_ids:
        return set()
    deposits = (
        (await db.execute(select(Deposit).where(Deposit.id.in_(deposit_ids)))).scalars().all()
    )
    cash_entry_ids: set[int] = set()
    for deposit in deposits:
        reference = deposit.bank_reference or f"DEP-ESP-{deposit.id}"
        result = await db.execute(
            select(CashRegister.id).where(
                CashRegister.source == CashEntrySource.DEPOSIT,
                CashRegister.date == deposit.date,
                CashRegister.amount == deposit.total_amount,
                CashRegister.reference == reference,
            )
        )
        cash_entry_ids.update(result.scalars().all())
    return cash_entry_ids


async def _derive_generated_entries(
    db: AsyncSession,
    *,
    invoice_ids: set[int],
    payment_ids: set[int],
    deposit_ids: set[int],
    salary_ids: set[int],
    bank_transaction_ids: set[int],
) -> set[int]:
    entry_ids: set[int] = set()
    source_groups = [
        (EntrySourceType.INVOICE, invoice_ids),
        (EntrySourceType.PAYMENT, payment_ids),
        (EntrySourceType.DEPOSIT, deposit_ids),
        (EntrySourceType.SALARY, salary_ids),
        (EntrySourceType.GESTION, bank_transaction_ids),
    ]
    for source_type, source_ids in source_groups:
        if not source_ids:
            continue
        result = await db.execute(
            select(AccountingEntry.id).where(
                AccountingEntry.source_type == source_type,
                AccountingEntry.source_id.in_(source_ids),
            )
        )
        entry_ids.update(result.scalars().all())
    return entry_ids


async def _find_deletable_contact_ids(
    db: AsyncSession,
    candidate_contact_ids: set[int],
    delete_object_ids: dict[str, set[int]],
) -> set[int]:
    if not candidate_contact_ids:
        return set()
    referenced_contact_ids: set[int] = set()
    source_queries = (
        select(Invoice.contact_id).where(
            Invoice.contact_id.in_(candidate_contact_ids),
            Invoice.id.not_in(delete_object_ids["invoice"] or {-1}),
        ),
        select(Payment.contact_id).where(
            Payment.contact_id.in_(candidate_contact_ids),
            Payment.id.not_in(delete_object_ids["payment"] or {-1}),
        ),
        select(CashRegister.contact_id).where(
            CashRegister.contact_id.in_(candidate_contact_ids),
            CashRegister.id.not_in(delete_object_ids["cash_register"] or {-1}),
        ),
    )
    for query in source_queries:
        result = await db.execute(query.distinct())
        referenced_contact_ids.update(
            contact_id for contact_id in result.scalars().all() if contact_id is not None
        )

    return candidate_contact_ids - referenced_contact_ids


async def _enrich_gestion_plan(db: AsyncSession, plan: _SelectiveResetPlan) -> None:
    derived_payment_ids = await _derive_invoice_payments(db, plan.delete_object_ids["invoice"])
    derived_payment_ids.update(
        await _derive_transaction_payments(db, plan.delete_object_ids["bank_transaction"])
    )
    derived_payment_ids -= plan.delete_object_ids["payment"]
    plan.derived_object_ids["payment"].update(derived_payment_ids)
    plan.delete_object_ids["payment"].update(derived_payment_ids)

    derived_deposit_ids = await _derive_payment_deposits(db, plan.delete_object_ids["payment"])
    plan.derived_object_ids["deposit"].update(derived_deposit_ids)
    plan.delete_object_ids["deposit"].update(derived_deposit_ids)

    derived_cash_ids = await _derive_payment_cash_entries(db, plan.delete_object_ids["payment"])
    derived_cash_ids.update(
        await _derive_deposit_cash_entries(db, plan.delete_object_ids["deposit"])
    )
    derived_cash_ids -= plan.delete_object_ids["cash_register"]
    plan.derived_object_ids["cash_register"].update(derived_cash_ids)
    plan.delete_object_ids["cash_register"].update(derived_cash_ids)

    derived_entry_ids = await _derive_generated_entries(
        db,
        invoice_ids=plan.delete_object_ids["invoice"],
        payment_ids=plan.delete_object_ids["payment"],
        deposit_ids=plan.delete_object_ids["deposit"],
        salary_ids=plan.delete_object_ids["salary"],
        bank_transaction_ids=plan.delete_object_ids["bank_transaction"],
    )
    derived_entry_ids -= plan.delete_object_ids["accounting_entry"]
    plan.derived_object_ids["accounting_entry"].update(derived_entry_ids)
    plan.delete_object_ids["accounting_entry"].update(derived_entry_ids)

    linked_transaction_ids = await _derive_transaction_ids_from_payments(
        db,
        plan.delete_object_ids["payment"],
    )
    plan.unlink_bank_transaction_ids.update(
        linked_transaction_ids - plan.delete_object_ids["bank_transaction"]
    )

    deletable_contact_ids = await _find_deletable_contact_ids(
        db,
        plan.root_object_ids["contact"],
        plan.delete_object_ids,
    )
    plan.delete_object_ids["contact"] = deletable_contact_ids


async def _derive_transaction_ids_from_payments(
    db: AsyncSession,
    payment_ids: set[int],
) -> set[int]:
    if not payment_ids:
        return set()
    result = await db.execute(
        select(bank_transaction_payments.c.transaction_id).where(
            bank_transaction_payments.c.payment_id.in_(payment_ids)
        )
    )
    transaction_ids = set(result.scalars().all())
    legacy_result = await db.execute(
        select(BankTransaction.id).where(BankTransaction.payment_id.in_(payment_ids))
    )
    transaction_ids.update(legacy_result.scalars().all())
    return transaction_ids


async def _build_selective_reset_plan(
    db: AsyncSession,
    payload: SelectiveResetRequest,
) -> _SelectiveResetPlan:
    plan = await _collect_import_scope_plan(db, payload)
    if payload.import_type == ImportLogType.GESTION:
        await _enrich_gestion_plan(db, plan)
    elif payload.import_type == ImportLogType.COMPTABILITE:
        plan.delete_object_ids["accounting_entry"].update(plan.root_object_ids["accounting_entry"])
    return plan


async def preview_selective_reset(
    db: AsyncSession,
    payload: SelectiveResetRequest,
) -> SelectiveResetPreviewRead:
    plan = await _build_selective_reset_plan(db, payload)
    return plan.to_preview()


async def _delete_model_ids(db: AsyncSession, model: type[Any], ids: set[int]) -> None:
    if not ids:
        return
    await db.execute(delete(model).where(model.id.in_(ids)))


async def _refresh_linked_bank_transactions(db: AsyncSession, tx_ids: set[int]) -> None:
    if not tx_ids:
        return
    transactions = (
        (await db.execute(select(BankTransaction).where(BankTransaction.id.in_(tx_ids))))
        .scalars()
        .all()
    )
    link_rows = (
        await db.execute(
            select(
                bank_transaction_payments.c.transaction_id,
                bank_transaction_payments.c.payment_id,
            ).where(bank_transaction_payments.c.transaction_id.in_(tx_ids))
        )
    ).all()
    payment_ids_by_tx: dict[int, list[int]] = defaultdict(list)
    for transaction_id, payment_id in link_rows:
        payment_ids_by_tx[int(transaction_id)].append(int(payment_id))

    linked_payment_ids = {payment_id for _, payment_id in link_rows}
    invoice_rows = (
        await db.execute(
            select(Payment.id, Invoice.number)
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .where(Payment.id.in_(linked_payment_ids or {-1}))
        )
    ).all()
    invoice_numbers: dict[int, str] = {
        int(payment_id): invoice_number for payment_id, invoice_number in invoice_rows
    }
    payment_reference_rows = (
        await db.execute(
            select(Payment.id, Payment.reference).where(Payment.id.in_(linked_payment_ids or {-1}))
        )
    ).all()
    payment_references: dict[int, str | None] = {
        int(payment_id): reference for payment_id, reference in payment_reference_rows
    }

    for tx in transactions:
        payment_ids = payment_ids_by_tx.get(tx.id, [])
        tx.reconciled = bool(payment_ids)
        tx.payment_id = payment_ids[0] if len(payment_ids) == 1 else None
        if not payment_ids:
            tx.reconciled_with = None
            continue
        labels = [
            invoice_numbers.get(payment_id)
            or payment_references.get(payment_id)
            or f"payment-{payment_id}"
            for payment_id in payment_ids
        ]
        tx.reconciled_with = labels[0] if len(labels) == 1 else f"{labels[0]} +{len(labels) - 1}"


async def apply_selective_reset(
    db: AsyncSession,
    payload: SelectiveResetRequest,
) -> SelectiveResetPreviewRead:
    plan = await _build_selective_reset_plan(db, payload)

    if plan.delete_object_ids["payment"]:
        await db.execute(
            delete(bank_transaction_payments).where(
                bank_transaction_payments.c.payment_id.in_(plan.delete_object_ids["payment"])
            )
        )
        linked_transactions = (
            (
                await db.execute(
                    select(BankTransaction).where(
                        BankTransaction.payment_id.in_(plan.delete_object_ids["payment"])
                    )
                )
            )
            .scalars()
            .all()
        )
        for transaction in linked_transactions:
            if transaction.id not in plan.delete_object_ids["bank_transaction"]:
                transaction.payment_id = None

    if plan.delete_object_ids["deposit"]:
        await db.execute(
            delete(deposit_payments).where(
                deposit_payments.c.deposit_id.in_(plan.delete_object_ids["deposit"])
            )
        )
    elif plan.delete_object_ids["payment"]:
        await db.execute(
            delete(deposit_payments).where(
                deposit_payments.c.payment_id.in_(plan.delete_object_ids["payment"])
            )
        )

    await _delete_model_ids(db, AccountingEntry, plan.delete_object_ids["accounting_entry"])
    await _delete_model_ids(db, CashRegister, plan.delete_object_ids["cash_register"])
    await _delete_model_ids(db, Deposit, plan.delete_object_ids["deposit"])
    await _delete_model_ids(db, Payment, plan.delete_object_ids["payment"])
    await _delete_model_ids(db, Invoice, plan.delete_object_ids["invoice"])
    await _delete_model_ids(db, Salary, plan.delete_object_ids["salary"])
    await _delete_model_ids(db, BankTransaction, plan.delete_object_ids["bank_transaction"])
    await _delete_model_ids(db, Contact, plan.delete_object_ids["contact"])
    await _refresh_linked_bank_transactions(db, plan.unlink_bank_transaction_ids)
    await _delete_model_ids(db, ImportRun, plan.import_run_ids)
    await _delete_model_ids(db, ImportLog, plan.import_log_ids)

    from backend.services.bank_service import recompute_bank_balances  # noqa: PLC0415
    from backend.services.cash_service import recompute_cash_balances  # noqa: PLC0415

    await recompute_bank_balances(db)
    await recompute_cash_balances(db)
    await db.commit()
    db.expunge_all()
    return plan.to_preview()


async def get_settings(db: AsyncSession) -> AppSettings:
    """Return the settings row, creating it with defaults if absent."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == _SETTINGS_ID))
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = AppSettings(id=_SETTINGS_ID)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


async def get_default_invoice_due_days(db: AsyncSession) -> int | None:
    """Return the configured default invoice due delay without mutating the session."""
    result = await db.execute(
        select(AppSettings.default_invoice_due_days).where(AppSettings.id == _SETTINGS_ID)
    )
    return result.scalar_one_or_none()


async def update_settings(db: AsyncSession, payload: AppSettingsUpdate) -> AppSettings:
    """Partially update settings with provided fields."""
    settings = await get_settings(db)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field_name, value)
    await db.commit()
    await db.refresh(settings)
    return settings


def _to_signed_cash_amount(entry: CashRegister | None) -> Decimal | None:
    if entry is None:
        return None
    amount = entry.amount
    return amount if entry.type == CashMovementType.IN else -amount


async def _get_default_system_opening_date(db: AsyncSession) -> date | None:
    result = await db.execute(select(FiscalYear.start_date).order_by(FiscalYear.start_date.asc()))
    return result.scalars().first()


async def get_treasury_system_opening(db: AsyncSession) -> TreasurySystemOpeningRead:
    default_date = await _get_default_system_opening_date(db)
    bank_entry = (
        (
            await db.execute(
                select(BankTransaction)
                .where(BankTransaction.source == BankTransactionSource.SYSTEM_OPENING)
                .order_by(BankTransaction.date.asc(), BankTransaction.id.asc())
            )
        )
        .scalars()
        .first()
    )
    cash_entry = (
        (
            await db.execute(
                select(CashRegister)
                .where(CashRegister.source == CashEntrySource.SYSTEM_OPENING)
                .order_by(CashRegister.date.asc(), CashRegister.id.asc())
            )
        )
        .scalars()
        .first()
    )

    return TreasurySystemOpeningRead(
        default_date=default_date,
        bank=SystemOpeningRead(
            configured=bank_entry is not None,
            date=bank_entry.date if bank_entry is not None else None,
            amount=bank_entry.amount if bank_entry is not None else None,
            reference=bank_entry.reference if bank_entry is not None else None,
        ),
        cash=SystemOpeningRead(
            configured=cash_entry is not None,
            date=cash_entry.date if cash_entry is not None else None,
            amount=_to_signed_cash_amount(cash_entry),
            reference=cash_entry.reference if cash_entry is not None else None,
        ),
    )


async def upsert_treasury_system_opening(
    db: AsyncSession, payload: TreasurySystemOpeningUpdate
) -> TreasurySystemOpeningRead:
    from backend.services.bank_service import recompute_bank_balances
    from backend.services.cash_service import recompute_cash_balances

    bank_entries = (
        (
            await db.execute(
                select(BankTransaction)
                .where(BankTransaction.source == BankTransactionSource.SYSTEM_OPENING)
                .order_by(BankTransaction.id.asc())
            )
        )
        .scalars()
        .all()
    )
    cash_entries = (
        (
            await db.execute(
                select(CashRegister)
                .where(CashRegister.source == CashEntrySource.SYSTEM_OPENING)
                .order_by(CashRegister.id.asc())
            )
        )
        .scalars()
        .all()
    )

    bank_entry: BankTransaction | None = bank_entries[0] if bank_entries else None
    cash_entry: CashRegister | None = cash_entries[0] if cash_entries else None

    for extra_bank_entry in bank_entries[1:]:
        await db.delete(extra_bank_entry)
    for extra_cash_entry in cash_entries[1:]:
        await db.delete(extra_cash_entry)

    if bank_entry is None:
        bank_entry = BankTransaction(
            date=payload.bank.date,
            amount=payload.bank.amount,
            reference=payload.bank.reference,
            description=CASH_SYSTEM_OPENING_DESCRIPTION,
            balance_after=Decimal("0"),
            source=BankTransactionSource.SYSTEM_OPENING,
        )
        db.add(bank_entry)
    else:
        bank_entry.date = payload.bank.date
        bank_entry.amount = payload.bank.amount
        bank_entry.reference = payload.bank.reference
        bank_entry.description = CASH_SYSTEM_OPENING_DESCRIPTION
        bank_entry.source = BankTransactionSource.SYSTEM_OPENING

    cash_amount = abs(payload.cash.amount)
    cash_type = CashMovementType.IN if payload.cash.amount > 0 else CashMovementType.OUT
    if cash_entry is None:
        cash_entry = CashRegister(
            date=payload.cash.date,
            amount=cash_amount,
            type=cash_type,
            reference=payload.cash.reference,
            description=CASH_SYSTEM_OPENING_DESCRIPTION,
            source=CashEntrySource.SYSTEM_OPENING,
            balance_after=Decimal("0"),
        )
        db.add(cash_entry)
    else:
        cash_entry.date = payload.cash.date
        cash_entry.amount = cash_amount
        cash_entry.type = cash_type
        cash_entry.reference = payload.cash.reference
        cash_entry.description = CASH_SYSTEM_OPENING_DESCRIPTION
        cash_entry.source = CashEntrySource.SYSTEM_OPENING

    await db.flush()
    await recompute_bank_balances(db)
    await recompute_cash_balances(db)
    await db.commit()

    return await get_treasury_system_opening(db)


# ---------------------------------------------------------------------------
# Database reset (test/demo helper)
# ---------------------------------------------------------------------------


async def reset_data(db: AsyncSession) -> dict[str, int]:
    """Delete every application table except users.

    Returns a mapping of table name → number of rows deleted.
    """
    deleted: dict[str, int] = {}

    for table in reversed(Base.metadata.sorted_tables):
        if table.name in _PRESERVED_TABLES:
            continue
        result = cast(CursorResult[Any], await db.execute(delete(table)))
        deleted[table.name] = result.rowcount or 0
        logger.debug("reset_data: deleted %d rows from %s", deleted[table.name], table.name)

    await db.commit()
    db.expunge_all()
    logger.info("reset_data: database reset completed while preserving users only")
    return deleted


async def bootstrap_accounting_setup(db: AsyncSession) -> dict[str, int]:
    """Seed accounts, rules, and the replay fiscal years used in local testing."""
    from backend.services.accounting_account import seed_default_accounts
    from backend.services.accounting_engine import seed_default_rules

    accounts_inserted = await seed_default_accounts(db)
    rules_inserted = await seed_default_rules(db)

    existing_names = {
        name for (name,) in (await db.execute(select(FiscalYear.name))).all() if name is not None
    }
    fiscal_years_created = 0
    for name, start_date, end_date in [
        ("2023", date(2023, 8, 1), date(2024, 7, 31)),
        ("2024", date(2024, 8, 1), date(2025, 7, 31)),
        ("2025", date(2025, 8, 1), date(2026, 7, 31)),
    ]:
        if name in existing_names:
            continue
        db.add(
            FiscalYear(
                name=name,
                start_date=start_date,
                end_date=end_date,
                status=FiscalYearStatus.OPEN,
            )
        )
        fiscal_years_created += 1

    if fiscal_years_created:
        await db.commit()

    return {
        "accounts_inserted": accounts_inserted,
        "rules_inserted": rules_inserted,
        "fiscal_years_created": fiscal_years_created,
    }
