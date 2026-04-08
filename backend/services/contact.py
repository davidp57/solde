"""Contact service — CRUD and search."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import Contact, ContactType
from backend.schemas.contact import ContactCreate, ContactUpdate


async def create_contact(db: AsyncSession, payload: ContactCreate) -> Contact:
    contact = Contact(**payload.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def get_contact(db: AsyncSession, contact_id: int) -> Contact | None:
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    return result.scalar_one_or_none()


async def list_contacts(
    db: AsyncSession,
    *,
    type: ContactType | None = None,
    search: str | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[Contact]:
    query = select(Contact)
    if active_only:
        query = query.where(Contact.is_active == True)  # noqa: E712
    if type is not None:
        query = query.where(Contact.type == type)
    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                Contact.nom.ilike(term),
                Contact.prenom.ilike(term),
                Contact.email.ilike(term),
            )
        )
    query = query.order_by(Contact.nom, Contact.prenom).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_contact(db: AsyncSession, contact: Contact, payload: ContactUpdate) -> Contact:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(db: AsyncSession, contact: Contact) -> None:
    """Soft-delete: mark as inactive rather than removing the row."""
    contact.is_active = False
    await db.commit()
