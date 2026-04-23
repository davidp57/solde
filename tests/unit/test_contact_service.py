"""Unit tests for the contact service."""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.contact import ContactCreate, ContactUpdate
from backend.services.contact import (
    create_contact,
    delete_contact,
    get_contact,
    get_contact_history,
    list_contacts,
    mark_creance_douteuse,
    update_contact,
)


class TestCreateContact:
    async def test_creates_client(self, db_session: AsyncSession):
        payload = ContactCreate(type=ContactType.CLIENT, nom="Dupont", prenom="Jean")
        contact = await create_contact(db_session, payload)
        assert contact.id is not None
        assert contact.nom == "Dupont"
        assert contact.prenom == "Jean"
        assert contact.type == ContactType.CLIENT
        assert contact.is_active is True

    async def test_creates_fournisseur(self, db_session: AsyncSession):
        payload = ContactCreate(type=ContactType.FOURNISSEUR, nom="ACME")
        contact = await create_contact(db_session, payload)
        assert contact.type == ContactType.FOURNISSEUR

    async def test_creates_with_all_fields(self, db_session: AsyncSession):
        payload = ContactCreate(
            type=ContactType.LES_DEUX,
            nom="Martin",
            prenom="Alice",
            email="alice@example.com",
            telephone="0612345678",
            adresse="1 rue de la Paix, 75001 Paris",
            notes="Bonne cliente",
        )
        contact = await create_contact(db_session, payload)
        assert contact.email == "alice@example.com"
        assert contact.telephone == "0612345678"

    async def test_strips_nom_whitespace(self, db_session: AsyncSession):
        payload = ContactCreate(type=ContactType.CLIENT, nom="  Dupont  ")
        contact = await create_contact(db_session, payload)
        assert contact.nom == "Dupont"


class TestGetContact:
    async def test_returns_existing_contact(self, db_session: AsyncSession):
        created = await create_contact(
            db_session, ContactCreate(type=ContactType.CLIENT, nom="Durand")
        )
        found = await get_contact(db_session, created.id)
        assert found is not None
        assert found.id == created.id

    async def test_returns_none_for_unknown_id(self, db_session: AsyncSession):
        result = await get_contact(db_session, 99999)
        assert result is None


class TestListContacts:
    async def test_returns_all_active_contacts(self, db_session: AsyncSession):
        await create_contact(db_session, ContactCreate(type=ContactType.CLIENT, nom="A"))
        await create_contact(db_session, ContactCreate(type=ContactType.FOURNISSEUR, nom="B"))
        contacts = await list_contacts(db_session)
        assert len(contacts) == 2

    async def test_filter_by_type(self, db_session: AsyncSession):
        await create_contact(db_session, ContactCreate(type=ContactType.CLIENT, nom="Client A"))
        await create_contact(
            db_session, ContactCreate(type=ContactType.FOURNISSEUR, nom="Fournisseur B")
        )
        clients = await list_contacts(db_session, type=ContactType.CLIENT)
        assert len(clients) == 1
        assert clients[0].nom == "Client A"

    async def test_search_by_nom(self, db_session: AsyncSession):
        await create_contact(db_session, ContactCreate(type=ContactType.CLIENT, nom="Dupont"))
        await create_contact(db_session, ContactCreate(type=ContactType.CLIENT, nom="Martin"))
        results = await list_contacts(db_session, search="dup")
        assert len(results) == 1
        assert results[0].nom == "Dupont"

    async def test_search_by_email(self, db_session: AsyncSession):
        await create_contact(
            db_session,
            ContactCreate(type=ContactType.CLIENT, nom="Durand", email="durand@example.com"),
        )
        await create_contact(db_session, ContactCreate(type=ContactType.CLIENT, nom="Martin"))
        results = await list_contacts(db_session, search="durand@")
        assert len(results) == 1

    async def test_excludes_inactive_by_default(self, db_session: AsyncSession):
        c = await create_contact(db_session, ContactCreate(type=ContactType.CLIENT, nom="Inactif"))
        await delete_contact(db_session, c)
        contacts = await list_contacts(db_session)
        assert len(contacts) == 0

    async def test_includes_inactive_when_requested(self, db_session: AsyncSession):
        c = await create_contact(db_session, ContactCreate(type=ContactType.CLIENT, nom="Inactif"))
        await delete_contact(db_session, c)
        contacts = await list_contacts(db_session, active_only=False)
        assert len(contacts) == 1

    async def test_pagination(self, db_session: AsyncSession):
        for i in range(5):
            await create_contact(
                db_session,
                ContactCreate(type=ContactType.CLIENT, nom=f"Contact {i:02d}"),
            )
        page = await list_contacts(db_session, skip=2, limit=2)
        assert len(page) == 2


class TestUpdateContact:
    async def test_partial_update_nom(self, db_session: AsyncSession):
        contact = await create_contact(
            db_session, ContactCreate(type=ContactType.CLIENT, nom="Ancien")
        )
        updated = await update_contact(db_session, contact, ContactUpdate(nom="Nouveau"))
        assert updated.nom == "Nouveau"
        assert updated.type == ContactType.CLIENT  # unchanged

    async def test_update_email(self, db_session: AsyncSession):
        contact = await create_contact(
            db_session, ContactCreate(type=ContactType.CLIENT, nom="Test")
        )
        updated = await update_contact(db_session, contact, ContactUpdate(email="new@example.com"))
        assert updated.email == "new@example.com"

    async def test_deactivate_contact(self, db_session: AsyncSession):
        contact = await create_contact(
            db_session, ContactCreate(type=ContactType.CLIENT, nom="Test")
        )
        updated = await update_contact(db_session, contact, ContactUpdate(is_active=False))
        assert updated.is_active is False


class TestDeleteContact:
    async def test_soft_delete(self, db_session: AsyncSession):
        contact = await create_contact(
            db_session, ContactCreate(type=ContactType.CLIENT, nom="À supprimer")
        )
        await delete_contact(db_session, contact)
        assert contact.is_active is False

    async def test_deleted_contact_not_in_list(self, db_session: AsyncSession):
        contact = await create_contact(
            db_session, ContactCreate(type=ContactType.CLIENT, nom="À supprimer")
        )
        await delete_contact(db_session, contact)
        contacts = await list_contacts(db_session)
        assert all(c.id != contact.id for c in contacts)


async def _make_contact(db: AsyncSession, nom: str = "Dupont") -> Contact:
    payload = ContactCreate(type=ContactType.CLIENT, nom=nom)
    return await create_contact(db, payload)


async def _make_invoice(
    db: AsyncSession,
    contact: Contact,
    *,
    number: str = "F-001",
    total: Decimal = Decimal("100.00"),
    paid: Decimal = Decimal("0"),
    status: InvoiceStatus = InvoiceStatus.SENT,
) -> Invoice:
    inv = Invoice(
        number=number,
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 6, 1),
        total_amount=total,
        paid_amount=paid,
        status=status,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return inv


class TestGetContactHistory:
    async def test_returns_none_for_unknown_contact(self, db_session: AsyncSession):
        result = await get_contact_history(db_session, 99999)
        assert result is None

    async def test_returns_empty_history_for_contact_with_no_invoices(
        self, db_session: AsyncSession
    ):
        contact = await _make_contact(db_session)
        history = await get_contact_history(db_session, contact.id)
        assert history is not None
        assert history.invoices == []
        assert history.payments == []
        assert history.total_invoiced == Decimal("0")
        assert history.total_paid == Decimal("0")
        assert history.total_due == Decimal("0")

    async def test_includes_invoices_in_history(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        await _make_invoice(db_session, contact, total=Decimal("200.00"))

        history = await get_contact_history(db_session, contact.id)
        assert history is not None
        assert len(history.invoices) == 1
        assert history.total_invoiced == Decimal("200.00")

    async def test_includes_payments_in_history(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        inv = await _make_invoice(
            db_session, contact, total=Decimal("200.00"), paid=Decimal("50.00")
        )
        pay = Payment(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("50.00"),
            date=date(2024, 7, 1),
            method=PaymentMethod.VIREMENT,
        )
        db_session.add(pay)
        await db_session.commit()

        history = await get_contact_history(db_session, contact.id)
        assert history is not None
        assert len(history.payments) == 1
        assert history.payments[0].amount == Decimal("50.00")
        assert history.total_due == Decimal("150.00")


class TestMarkCreanceDouteuse:
    async def test_returns_none_for_unknown_contact(self, db_session: AsyncSession):
        result = await mark_creance_douteuse(db_session, 99999)
        assert result is None

    async def test_returns_none_when_no_balance_due(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        await _make_invoice(
            db_session,
            contact,
            total=Decimal("100.00"),
            paid=Decimal("100.00"),
            status=InvoiceStatus.PAID,
        )
        result = await mark_creance_douteuse(db_session, contact.id)
        assert result is None

    async def test_creates_transfer_entries(self, db_session: AsyncSession):
        contact = await _make_contact(db_session)
        # Create a fiscal year so entries get linked
        fy = FiscalYear(
            name="2024",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status=FiscalYearStatus.OPEN,
        )
        db_session.add(fy)
        await db_session.commit()

        await _make_invoice(
            db_session,
            contact,
            total=Decimal("500.00"),
            paid=Decimal("200.00"),
            status=InvoiceStatus.PARTIAL,
        )

        result = await mark_creance_douteuse(db_session, contact.id)
        assert result is not None
        debit_entry, credit_entry = result

        assert debit_entry.debit == Decimal("300.00")
        assert debit_entry.credit == Decimal("0")
        assert f"416{contact.id:04d}" in debit_entry.account_number

        assert credit_entry.credit == Decimal("300.00")
        assert credit_entry.debit == Decimal("0")
        assert f"411{contact.id:04d}" in credit_entry.account_number
