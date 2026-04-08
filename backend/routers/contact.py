"""Contacts API router — CRUD and search."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.contact import ContactType
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from backend.services import contact as contact_service

router = APIRouter(prefix="/contacts", tags=["contacts"])

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=list[ContactRead])
async def list_contacts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    type: ContactType | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ContactRead]:
    """List contacts with optional filters."""
    contacts = await contact_service.list_contacts(
        db,
        type=type,
        search=search,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return contacts  # type: ignore[return-value]


@router.post("/", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> ContactRead:
    """Create a new contact."""
    return await contact_service.create_contact(db, payload)  # type: ignore[return-value]


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(
    contact_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> ContactRead:
    """Get a single contact by ID."""
    contact = await contact_service.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact  # type: ignore[return-value]


@router.put("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> ContactRead:
    """Partially update a contact."""
    contact = await contact_service.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return await contact_service.update_contact(db, contact, payload)  # type: ignore[return-value]


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> None:
    """Soft-delete a contact (marks as inactive)."""
    contact = await contact_service.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    await contact_service.delete_contact(db, contact)
