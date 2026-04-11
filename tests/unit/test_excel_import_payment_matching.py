"""Unit tests for Excel import payment matching helpers."""

from __future__ import annotations

from dataclasses import dataclass

from backend.services.excel_import_payment_matching import (
    PaymentMatchCandidate,
    candidate_key_for_invoice,
    dedupe_payment_candidates,
    make_workbook_invoice_candidate,
    resolve_candidates_by_contact_name,
    resolve_candidates_by_invoice_ref,
    resolve_payment_match,
)


@dataclass(slots=True)
class _InvoiceRow:
    source_row_number: int
    invoice_number: str | None
    contact_name: str


@dataclass(slots=True)
class _PaymentRow:
    invoice_ref: str
    contact_name: str


def _candidate(
    *,
    key: str,
    invoice_number: str | None,
    contact_name: str,
    invoice_id: int = 1,
    contact_id: int = 1,
) -> PaymentMatchCandidate:
    return PaymentMatchCandidate(
        candidate_key=key,
        invoice_id=invoice_id,
        contact_id=contact_id,
        invoice_type=None,
        invoice_number=invoice_number,
        contact_name=contact_name,
    )


def test_candidate_key_for_invoice_prefers_invoice_number() -> None:
    assert (
        candidate_key_for_invoice(invoice_number="2025-0131", fallback="x") == "invoice:2025-0131"
    )
    assert candidate_key_for_invoice(invoice_number=None, fallback="x") == "x"


def test_dedupe_payment_candidates_keeps_first_candidate_key() -> None:
    first = _candidate(key="invoice:2025-0131", invoice_number="2025-0131", contact_name="Alice")
    second = _candidate(key="invoice:2025-0131", invoice_number="2025-0131", contact_name="Bob")

    assert dedupe_payment_candidates([first, second]) == [first]


def test_resolve_candidates_by_invoice_ref_prefers_exact_match() -> None:
    exact = _candidate(key="invoice:2025-0131", invoice_number="2025-0131", contact_name="Alice")
    partial = _candidate(
        key="invoice:2025-01310", invoice_number="2025-01310", contact_name="Alice"
    )

    assert resolve_candidates_by_invoice_ref([partial, exact], "2025-0131") == [exact]


def test_resolve_candidates_by_contact_name_supports_exact_match() -> None:
    alice = _candidate(key="invoice:a", invoice_number="A", contact_name="Alice Dupont")
    bob = _candidate(key="invoice:b", invoice_number="B", contact_name="Bob Martin")

    assert resolve_candidates_by_contact_name([alice, bob], "Alice Dupont") == [alice]


def test_make_workbook_invoice_candidate_uses_workbook_fallback() -> None:
    candidate = make_workbook_invoice_candidate(_InvoiceRow(7, None, "Alice Dupont"))

    assert candidate.candidate_key == "workbook-row:7"
    assert candidate.contact_name == "Alice Dupont"


def test_resolve_payment_match_returns_unique_invoice_match() -> None:
    candidate = _candidate(
        key="invoice:2025-0131", invoice_number="2025-0131", contact_name="Alice"
    )
    resolution = resolve_payment_match(_PaymentRow("2025-0131", "Alice"), [candidate])

    assert resolution.status == "matched"
    assert resolution.candidate == candidate


def test_resolve_payment_match_detects_ambiguous_reference() -> None:
    first = _candidate(
        key="invoice:2025-0131-a", invoice_number="2025-0131-A", contact_name="Alice"
    )
    second = _candidate(
        key="invoice:2025-0131-b", invoice_number="2025-0131-B", contact_name="Alice"
    )

    resolution = resolve_payment_match(_PaymentRow("2025-0131", "Alice"), [first, second])

    assert resolution.status == "ambiguous"
    assert resolution.message == "reference facture ambigue : plusieurs factures correspondent"


def test_resolve_payment_match_falls_back_to_contact_and_missing() -> None:
    candidate = _candidate(
        key="invoice:2025-0200", invoice_number="2025-0200", contact_name="Alice Dupont"
    )

    matched = resolve_payment_match(_PaymentRow("", "Alice Dupont"), [candidate])
    missing = resolve_payment_match(_PaymentRow("", "Charlie"), [candidate])

    assert matched.status == "matched"
    assert missing.status == "missing"
    assert missing.message == "paiement impossible a rapprocher a une facture existante ou importee"
