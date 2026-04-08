"""Unit tests for the contact service."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import ContactType
from backend.schemas.contact import ContactCreate, ContactUpdate
from backend.services.contact import (
    create_contact,
    delete_contact,
    get_contact,
    list_contacts,
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
                db_session, ContactCreate(type=ContactType.CLIENT, nom=f"Contact {i:02d}")
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
