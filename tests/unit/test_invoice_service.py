"""Unit tests for the invoice service."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.contact import Contact, ContactType
from backend.models.invoice import InvoiceLabel, InvoiceLineType, InvoiceStatus, InvoiceType
from backend.schemas.invoice import InvoiceCreate, InvoiceLineCreate, InvoiceUpdate
from backend.schemas.payment import PaymentCreate
from backend.schemas.settings import AppSettingsUpdate
from backend.services.accounting_engine import seed_default_rules
from backend.services.invoice import (
    InvoiceDeleteError,
    InvoiceStatusError,
    InvoiceUpdateError,
    create_invoice,
    delete_invoice,
    duplicate_invoice,
    get_invoice,
    list_invoices,
    update_invoice,
    update_invoice_status,
)
from backend.services.payment import create_payment
from backend.services.settings import update_settings


async def _make_contact(db: AsyncSession, nom: str = "Test") -> Contact:
    contact = Contact(type=ContactType.CLIENT, nom=nom, is_active=True)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def _make_invoice(
    db: AsyncSession,
    *,
    invoice_type: InvoiceType = InvoiceType.CLIENT,
    lines: list[InvoiceLineCreate] | None = None,
    total_amount: Decimal | None = None,
    invoice_date: date | None = None,
    label: InvoiceLabel | None = None,
) -> object:
    contact = await _make_contact(db)
    payload = InvoiceCreate(
        type=invoice_type,
        contact_id=contact.id,
        date=invoice_date or date(2025, 6, 1),
        label=label,
        lines=lines or [],
        total_amount=total_amount,
    )
    return await create_invoice(db, payload)


class TestGenerateInvoiceNumber:
    async def test_first_client_invoice_of_year(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        assert invoice.number == "2025-001"  # type: ignore[union-attr]

    async def test_second_client_invoice_increments(self, db_session: AsyncSession):
        await _make_invoice(db_session)
        invoice2 = await _make_invoice(db_session)
        assert invoice2.number == "2025-002"  # type: ignore[union-attr]

    async def test_supplier_invoice_uses_f_prefix(self, db_session: AsyncSession):
        invoice = await _make_invoice(
            db_session,
            invoice_type=InvoiceType.FOURNISSEUR,
            total_amount=Decimal("100.00"),
        )
        assert invoice.number.startswith("FF-")  # type: ignore[union-attr]

    async def test_client_and_supplier_have_independent_sequences(self, db_session: AsyncSession):
        await _make_invoice(db_session)
        supplier = await _make_invoice(
            db_session,
            invoice_type=InvoiceType.FOURNISSEUR,
            total_amount=Decimal("50.00"),
        )
        assert supplier.number.startswith("FF-")  # type: ignore[union-attr]

    async def test_year_changes_resets_sequence(self, db_session: AsyncSession):
        await _make_invoice(db_session, invoice_date=date(2024, 12, 1))
        invoice_2025 = await _make_invoice(db_session, invoice_date=date(2025, 1, 15))
        assert invoice_2025.number == "2025-001"  # type: ignore[union-attr]

    async def test_custom_client_template(self, db_session: AsyncSession):
        await update_settings(
            db_session,
            AppSettingsUpdate(
                client_invoice_number_template="FAC{year}/{seq}",
                client_invoice_seq_digits=4,
            ),
        )
        invoice = await _make_invoice(db_session)
        assert invoice.number == "FAC2025/0001"  # type: ignore[union-attr]

    async def test_custom_supplier_template(self, db_session: AsyncSession):
        await update_settings(
            db_session,
            AppSettingsUpdate(supplier_invoice_number_template="FOURN-%Y%m"),
        )
        invoice = await _make_invoice(
            db_session, invoice_type=InvoiceType.FOURNISSEUR, total_amount=Decimal("100.00")
        )
        assert invoice.number.startswith("FOURN-")  # type: ignore[union-attr]


class TestCreateInvoice:
    async def test_creates_with_lines_and_computes_total(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        lines = [
            InvoiceLineCreate(
                description="Cours maths",
                quantity=Decimal("2"),
                unit_price=Decimal("30.00"),
            ),
            InvoiceLineCreate(
                description="Adhésion",
                quantity=Decimal("1"),
                unit_price=Decimal("20.00"),
            ),
        ]
        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            lines=lines,
        )
        invoice = await create_invoice(db_session, payload)
        assert invoice.total_amount == Decimal("80.00")
        assert len(invoice.lines) == 2
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.label == InvoiceLabel.CS_ADHESION
        assert [line.line_type for line in invoice.lines] == [
            InvoiceLineType.COURSE,
            InvoiceLineType.ADHESION,
        ]

    async def test_creates_supplier_invoice_with_total_amount(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        payload = InvoiceCreate(
            type=InvoiceType.FOURNISSEUR,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            total_amount=Decimal("250.00"),
            reference="INV-2025-123",
        )
        invoice = await create_invoice(db_session, payload)
        assert invoice.total_amount == Decimal("250.00")
        assert invoice.reference == "INV-2025-123"
        assert invoice.paid_amount == Decimal("0")

    async def test_uses_default_due_date_when_setting_is_configured(self, db_session: AsyncSession):
        await update_settings(db_session, AppSettingsUpdate(default_invoice_due_days=30))
        contact = await _make_contact(db_session)

        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            lines=[
                InvoiceLineCreate(
                    description="Cours maths",
                    quantity=Decimal("1"),
                    unit_price=Decimal("50.00"),
                )
            ],
        )

        invoice = await create_invoice(db_session, payload)

        assert invoice.due_date == date(2025, 10, 1)

    async def test_keeps_explicit_due_date_over_default(self, db_session: AsyncSession):
        await update_settings(db_session, AppSettingsUpdate(default_invoice_due_days=30))
        contact = await _make_contact(db_session)

        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            due_date=date(2025, 9, 15),
            lines=[
                InvoiceLineCreate(
                    description="Cours maths",
                    quantity=Decimal("1"),
                    unit_price=Decimal("50.00"),
                )
            ],
        )

        invoice = await create_invoice(db_session, payload)

        assert invoice.due_date == date(2025, 9, 15)

    async def test_default_status_is_draft(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        assert invoice.status == InvoiceStatus.DRAFT  # type: ignore[union-attr]

    async def test_default_paid_amount_is_zero(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        assert invoice.paid_amount == Decimal("0")  # type: ignore[union-attr]

    async def test_line_amount_is_computed(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        lines = [
            InvoiceLineCreate(
                description="Cours", quantity=Decimal("3"), unit_price=Decimal("25.00")
            )
        ]
        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            lines=lines,
        )
        invoice = await create_invoice(db_session, payload)
        assert invoice.lines[0].amount == Decimal("75.00")
        assert invoice.lines[0].line_type == InvoiceLineType.COURSE

    async def test_client_lines_mark_explicit_breakdown(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                InvoiceLineCreate(
                    description="Cours de soutien",
                    quantity=Decimal("1"),
                    unit_price=Decimal("130.00"),
                ),
                InvoiceLineCreate(
                    description="Adhesion annuelle",
                    quantity=Decimal("1"),
                    unit_price=Decimal("30.00"),
                ),
            ],
        )

        invoice = await create_invoice(db_session, payload)

        assert invoice.has_explicit_breakdown is True

    async def test_single_client_line_does_not_mark_explicit_breakdown(
        self, db_session: AsyncSession
    ):
        contact = await _make_contact(db_session)
        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                InvoiceLineCreate(
                    description="Cours de soutien",
                    quantity=Decimal("1"),
                    unit_price=Decimal("130.00"),
                )
            ],
        )

        invoice = await create_invoice(db_session, payload)

        assert invoice.has_explicit_breakdown is False


class TestGetInvoice:
    async def test_returns_invoice_with_lines(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        lines = [
            InvoiceLineCreate(
                description="Cours", quantity=Decimal("1"), unit_price=Decimal("40.00")
            )
        ]
        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            lines=lines,
        )
        created = await create_invoice(db_session, payload)
        found = await get_invoice(db_session, created.id)
        assert found is not None
        assert len(found.lines) == 1

    async def test_returns_none_for_unknown_id(self, db_session: AsyncSession):
        result = await get_invoice(db_session, 99999)
        assert result is None


class TestListInvoices:
    async def test_filter_by_type(self, db_session: AsyncSession):
        await _make_invoice(db_session)
        await _make_invoice(
            db_session,
            invoice_type=InvoiceType.FOURNISSEUR,
            total_amount=Decimal("100.00"),
        )
        clients = await list_invoices(db_session, invoice_type=InvoiceType.CLIENT)
        assert len(clients) == 1
        assert clients[0].type == InvoiceType.CLIENT

    async def test_filter_by_status(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        await update_invoice_status(db_session, invoice, InvoiceStatus.SENT)  # type: ignore[arg-type]
        drafts = await list_invoices(db_session, status=InvoiceStatus.DRAFT)
        sents = await list_invoices(db_session, status=InvoiceStatus.SENT)
        assert len(drafts) == 0
        assert len(sents) == 1

    async def test_filter_by_contact_id(self, db_session: AsyncSession):
        contact1 = await _make_contact(db_session, "Alpha")
        contact2 = await _make_contact(db_session, "Beta")
        p1 = InvoiceCreate(type=InvoiceType.CLIENT, contact_id=contact1.id, date=date(2025, 9, 1))
        p2 = InvoiceCreate(type=InvoiceType.CLIENT, contact_id=contact2.id, date=date(2025, 9, 1))
        await create_invoice(db_session, p1)
        await create_invoice(db_session, p2)
        results = await list_invoices(db_session, contact_id=contact1.id)
        assert len(results) == 1

    async def test_filter_by_year(self, db_session: AsyncSession):
        await _make_invoice(db_session, invoice_date=date(2024, 6, 1))
        await _make_invoice(db_session, invoice_date=date(2025, 6, 1))
        results_2025 = await list_invoices(db_session, year=2025)
        assert len(results_2025) == 1
        assert results_2025[0].date.year == 2025


class TestUpdateInvoice:
    async def test_update_description(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        updated = await update_invoice(
            db_session,
            invoice,
            InvoiceUpdate(description="New description"),  # type: ignore[arg-type]
        )
        assert updated.description == "New description"

    async def test_replace_lines_recalculates_total(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        lines_orig = [
            InvoiceLineCreate(
                description="Cours", quantity=Decimal("1"), unit_price=Decimal("30.00")
            )
        ]
        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            lines=lines_orig,
        )
        invoice = await create_invoice(db_session, payload)
        new_lines = [
            InvoiceLineCreate(
                description="Cours A",
                quantity=Decimal("2"),
                unit_price=Decimal("25.00"),
            ),
            InvoiceLineCreate(
                description="Adhésion",
                quantity=Decimal("1"),
                unit_price=Decimal("15.00"),
            ),
        ]
        updated = await update_invoice(
            db_session,
            invoice,
            InvoiceUpdate(lines=new_lines),  # type: ignore[arg-type]
        )
        assert updated.total_amount == Decimal("65.00")
        assert len(updated.lines) == 2
        assert updated.label == InvoiceLabel.CS_ADHESION
        assert [line.line_type for line in updated.lines] == [
            InvoiceLineType.COURSE,
            InvoiceLineType.ADHESION,
        ]

    async def test_update_client_lines_marks_explicit_breakdown(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)

        updated = await update_invoice(
            db_session,
            invoice,
            InvoiceUpdate(
                label=InvoiceLabel.CS_ADHESION,
                lines=[
                    InvoiceLineCreate(
                        description="Cours de soutien",
                        quantity=Decimal("1"),
                        unit_price=Decimal("130.00"),
                    ),
                    InvoiceLineCreate(
                        description="Adhesion annuelle",
                        quantity=Decimal("1"),
                        unit_price=Decimal("30.00"),
                    ),
                ],
            ),
        )

        assert updated.has_explicit_breakdown is True

    async def test_update_single_client_line_clears_explicit_breakdown(
        self, db_session: AsyncSession
    ):
        invoice = await _make_invoice(
            db_session,
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                InvoiceLineCreate(
                    description="Cours de soutien",
                    quantity=Decimal("1"),
                    unit_price=Decimal("130.00"),
                ),
                InvoiceLineCreate(
                    description="Adhesion annuelle",
                    quantity=Decimal("1"),
                    unit_price=Decimal("30.00"),
                ),
            ],
        )

        updated = await update_invoice(
            db_session,
            invoice,
            InvoiceUpdate(
                lines=[
                    InvoiceLineCreate(
                        description="Cours de soutien",
                        quantity=Decimal("1"),
                        unit_price=Decimal("160.00"),
                    )
                ]
            ),
        )

        assert updated.has_explicit_breakdown is False

    async def test_update_sent_invoice_regenerates_generated_entries(
        self, db_session: AsyncSession
    ):
        await seed_default_rules(db_session)
        contact = await _make_contact(db_session)
        invoice = await create_invoice(
            db_session,
            InvoiceCreate(
                type=InvoiceType.CLIENT,
                contact_id=contact.id,
                date=date(2025, 9, 1),
                lines=[
                    InvoiceLineCreate(
                        description="Cours",
                        quantity=Decimal("1"),
                        unit_price=Decimal("130.00"),
                    ),
                    InvoiceLineCreate(
                        description="Adhésion",
                        quantity=Decimal("1"),
                        unit_price=Decimal("30.00"),
                    ),
                ],
            ),
        )
        await update_invoice_status(db_session, invoice, InvoiceStatus.SENT)

        initial_entries = list(
            (
                await db_session.execute(
                    select(AccountingEntry)
                    .where(AccountingEntry.source_type == EntrySourceType.INVOICE)
                    .where(AccountingEntry.source_id == invoice.id)
                    .order_by(AccountingEntry.entry_number.asc())
                )
            ).scalars()
        )
        assert len(initial_entries) == 3

        updated = await update_invoice(
            db_session,
            invoice,
            InvoiceUpdate(
                lines=[
                    InvoiceLineCreate(
                        description="Cours",
                        quantity=Decimal("1"),
                        unit_price=Decimal("150.00"),
                    )
                ]
            ),
        )

        regenerated_entries = list(
            (
                await db_session.execute(
                    select(AccountingEntry)
                    .where(AccountingEntry.source_type == EntrySourceType.INVOICE)
                    .where(AccountingEntry.source_id == invoice.id)
                    .order_by(AccountingEntry.entry_number.asc())
                )
            ).scalars()
        )

        assert updated.status == InvoiceStatus.SENT
        assert updated.total_amount == Decimal("150.00")
        assert len(regenerated_entries) == 2
        assert {entry.account_number for entry in regenerated_entries} == {"411100", "706110"}
        assert any(entry.debit == Decimal("150.00") for entry in regenerated_entries)
        assert any(entry.credit == Decimal("150.00") for entry in regenerated_entries)

    async def test_update_paid_invoice_is_blocked(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        invoice = await create_invoice(
            db_session,
            InvoiceCreate(
                type=InvoiceType.CLIENT,
                contact_id=contact.id,
                date=date(2025, 9, 1),
                lines=[
                    InvoiceLineCreate(
                        description="Cours",
                        quantity=Decimal("1"),
                        unit_price=Decimal("130.00"),
                    )
                ],
            ),
        )
        await update_invoice_status(db_session, invoice, InvoiceStatus.SENT)
        await create_payment(
            db_session,
            PaymentCreate(
                invoice_id=invoice.id,
                contact_id=contact.id,
                amount=Decimal("130.00"),
                date=date(2025, 9, 2),
                method="cheque",
            ),
        )
        refreshed = await get_invoice(db_session, invoice.id)
        assert refreshed is not None
        assert refreshed.status == InvoiceStatus.PAID

        with pytest.raises(InvoiceUpdateError, match="cannot be edited"):
            await update_invoice(
                db_session,
                refreshed,
                InvoiceUpdate(description="Nouvelle description"),
            )


class TestStatusChange:
    async def test_draft_to_sent(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        updated = await update_invoice_status(db_session, invoice, InvoiceStatus.SENT)  # type: ignore[arg-type]
        assert updated.status == InvoiceStatus.SENT

    async def test_invalid_transition_raises(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        await update_invoice_status(db_session, invoice, InvoiceStatus.PAID)  # type: ignore[arg-type]
        with pytest.raises(InvoiceStatusError):
            await update_invoice_status(db_session, invoice, InvoiceStatus.SENT)  # type: ignore[arg-type]

    async def test_valid_partial_to_paid(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        await update_invoice_status(db_session, invoice, InvoiceStatus.SENT)  # type: ignore[arg-type]
        await update_invoice_status(db_session, invoice, InvoiceStatus.PARTIAL)  # type: ignore[arg-type]
        result = await update_invoice_status(db_session, invoice, InvoiceStatus.PAID)  # type: ignore[arg-type]
        assert result.status == InvoiceStatus.PAID


class TestDuplicate:
    async def test_creates_new_draft_with_new_number(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        copy = await duplicate_invoice(db_session, invoice)  # type: ignore[arg-type]
        assert copy.status == InvoiceStatus.DRAFT
        assert copy.number != invoice.number  # type: ignore[union-attr]
        assert copy.number.startswith(str(date.today().year))

    async def test_copied_invoice_has_same_contact(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        copy = await duplicate_invoice(db_session, invoice)  # type: ignore[arg-type]
        assert copy.contact_id == invoice.contact_id  # type: ignore[union-attr]

    async def test_copied_invoice_has_same_lines(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        lines = [
            InvoiceLineCreate(
                description="Cours", quantity=Decimal("2"), unit_price=Decimal("30.00")
            )
        ]
        payload = InvoiceCreate(
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 9, 1),
            lines=lines,
        )
        invoice = await create_invoice(db_session, payload)
        copy = await duplicate_invoice(db_session, invoice)
        assert len(copy.lines) == 1
        assert copy.lines[0].description == "Cours"
        assert copy.lines[0].line_type == InvoiceLineType.COURSE

    async def test_copy_paid_amount_is_zero(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        copy = await duplicate_invoice(db_session, invoice)  # type: ignore[arg-type]
        assert copy.paid_amount == Decimal("0")

    async def test_duplicate_preserves_explicit_breakdown_for_cs_a_lines(
        self, db_session: AsyncSession
    ):
        invoice = await _make_invoice(
            db_session,
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                InvoiceLineCreate(
                    description="Cours de soutien",
                    quantity=Decimal("1"),
                    unit_price=Decimal("130.00"),
                ),
                InvoiceLineCreate(
                    description="Adhesion annuelle",
                    quantity=Decimal("1"),
                    unit_price=Decimal("30.00"),
                ),
            ],
        )

        copy = await duplicate_invoice(db_session, invoice)  # type: ignore[arg-type]

        assert copy.has_explicit_breakdown is True

    async def test_duplicate_single_client_line_does_not_mark_explicit_breakdown(
        self, db_session: AsyncSession
    ):
        invoice = await _make_invoice(
            db_session,
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                InvoiceLineCreate(
                    description="Cours de soutien",
                    quantity=Decimal("1"),
                    unit_price=Decimal("130.00"),
                )
            ],
        )

        copy = await duplicate_invoice(db_session, invoice)  # type: ignore[arg-type]

        assert copy.has_explicit_breakdown is False


class TestDeleteInvoice:
    async def test_delete_draft_invoice(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        await delete_invoice(db_session, invoice)  # type: ignore[arg-type]
        assert await get_invoice(db_session, invoice.id) is None  # type: ignore[union-attr]

    async def test_cannot_delete_non_draft(self, db_session: AsyncSession):
        invoice = await _make_invoice(db_session)
        await update_invoice_status(db_session, invoice, InvoiceStatus.SENT)  # type: ignore[arg-type]
        with pytest.raises(InvoiceDeleteError):
            await delete_invoice(db_session, invoice)  # type: ignore[arg-type]
