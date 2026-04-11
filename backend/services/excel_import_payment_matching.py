"""Payment matching helpers for historical Excel import."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import_parsing import normalize_text
from backend.services.excel_import_policy import (
    PAYMENT_AMBIGUOUS_CONTACT_MESSAGE,
    PAYMENT_AMBIGUOUS_REFERENCE_MESSAGE,
    PAYMENT_MISSING_MATCH_MESSAGE,
)


@dataclass(slots=True)
class PaymentMatchCandidate:
    """Candidate invoice target for a payment match."""

    candidate_key: str
    invoice_id: int | None
    contact_id: int | None
    invoice_type: Any | None
    invoice_number: str | None
    contact_name: str


@dataclass(slots=True)
class PaymentMatchResolution:
    """Resolution outcome for a payment match."""

    status: str
    candidate: PaymentMatchCandidate | None = None
    message: str | None = None


def dedupe_payment_candidates(
    candidates: list[PaymentMatchCandidate],
) -> list[PaymentMatchCandidate]:
    deduped: dict[str, PaymentMatchCandidate] = {}
    for candidate in candidates:
        deduped.setdefault(candidate.candidate_key, candidate)
    return list(deduped.values())


def candidate_key_for_invoice(*, invoice_number: str | None, fallback: str) -> str:
    if invoice_number:
        return f"invoice:{normalize_text(invoice_number)}"
    return fallback


def resolve_candidates_by_invoice_ref(
    candidates: list[PaymentMatchCandidate], invoice_ref: str
) -> list[PaymentMatchCandidate]:
    normalized_ref = normalize_text(invoice_ref)
    exact_matches = [
        candidate
        for candidate in candidates
        if candidate.invoice_number and normalize_text(candidate.invoice_number) == normalized_ref
    ]
    if exact_matches:
        return dedupe_payment_candidates(exact_matches)

    partial_matches = [
        candidate
        for candidate in candidates
        if candidate.invoice_number and normalized_ref in normalize_text(candidate.invoice_number)
    ]
    return dedupe_payment_candidates(partial_matches)


def resolve_candidates_by_contact_name(
    candidates: list[PaymentMatchCandidate], contact_name: str
) -> list[PaymentMatchCandidate]:
    normalized_contact_name = normalize_text(contact_name)
    exact_matches = [
        candidate
        for candidate in candidates
        if normalize_text(candidate.contact_name) == normalized_contact_name
    ]
    if exact_matches:
        return dedupe_payment_candidates(exact_matches)

    partial_matches = [
        candidate
        for candidate in candidates
        if normalized_contact_name in normalize_text(candidate.contact_name)
    ]
    return dedupe_payment_candidates(partial_matches)


def make_workbook_invoice_candidate(invoice_row: Any) -> PaymentMatchCandidate:
    return PaymentMatchCandidate(
        candidate_key=candidate_key_for_invoice(
            invoice_number=invoice_row.invoice_number,
            fallback=f"workbook-row:{invoice_row.source_row_number}",
        ),
        invoice_id=None,
        contact_id=None,
        invoice_type=None,
        invoice_number=invoice_row.invoice_number,
        contact_name=invoice_row.contact_name,
    )


async def load_database_payment_candidates(db: AsyncSession) -> list[PaymentMatchCandidate]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.invoice import Invoice  # noqa: PLC0415

    result = await db.execute(
        select(Invoice, Contact).join(Contact, Invoice.contact_id == Contact.id)
    )
    return [
        PaymentMatchCandidate(
            candidate_key=candidate_key_for_invoice(
                invoice_number=invoice.number,
                fallback=f"db-invoice:{invoice.id}",
            ),
            invoice_id=invoice.id,
            contact_id=contact.id,
            invoice_type=invoice.type,
            invoice_number=invoice.number,
            contact_name=contact.nom,
        )
        for invoice, contact in result.all()
    ]


def resolve_payment_match(
    payment_row: Any,
    all_candidates: list[PaymentMatchCandidate],
) -> PaymentMatchResolution:
    if payment_row.invoice_ref:
        ref_matches = resolve_candidates_by_invoice_ref(all_candidates, payment_row.invoice_ref)
        if len(ref_matches) == 1:
            return PaymentMatchResolution(status="matched", candidate=ref_matches[0])
        if len(ref_matches) > 1:
            return PaymentMatchResolution(
                status="ambiguous",
                message=PAYMENT_AMBIGUOUS_REFERENCE_MESSAGE,
            )

    if payment_row.contact_name:
        contact_matches = resolve_candidates_by_contact_name(
            all_candidates, payment_row.contact_name
        )
        if len(contact_matches) == 1:
            return PaymentMatchResolution(status="matched", candidate=contact_matches[0])
        if len(contact_matches) > 1:
            return PaymentMatchResolution(
                status="ambiguous",
                message=PAYMENT_AMBIGUOUS_CONTACT_MESSAGE,
            )

    return PaymentMatchResolution(
        status="missing",
        message=PAYMENT_MISSING_MATCH_MESSAGE,
    )


async def resolve_payment_match_with_database(
    db: AsyncSession,
    payment_row: Any,
    workbook_candidates: list[PaymentMatchCandidate] | None = None,
) -> PaymentMatchResolution:
    all_candidates = list(workbook_candidates or [])
    all_candidates.extend(await load_database_payment_candidates(db))
    return resolve_payment_match(payment_row, all_candidates)
