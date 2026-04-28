"""Contact model — clients, fournisseurs, or both."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base
from backend.models.types import DecimalType

_Decimal = Decimal


class ContactType(StrEnum):
    CLIENT = "client"
    FOURNISSEUR = "fournisseur"
    LES_DEUX = "les_deux"
    EMPLOYE = "employe"


class ContractType(StrEnum):
    CDI = "cdi"
    CDD = "cdd"


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[ContactType] = mapped_column(String(20), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prenom: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    telephone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    adresse: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Employee contract fields (only relevant when type == EMPLOYE)
    contract_type: Mapped[ContractType | None] = mapped_column(String(10), nullable=True)
    base_gross: Mapped[_Decimal | None] = mapped_column(DecimalType(10, 2), nullable=True)
    base_hours: Mapped[_Decimal | None] = mapped_column(DecimalType(8, 2), nullable=True)
    hourly_rate: Mapped[_Decimal | None] = mapped_column(DecimalType(10, 2), nullable=True)

    # Flag for freelance contractors (auto-entrepreneurs) — used in workforce cost view
    is_contractor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Child / other-parent fields (optional, only relevant for CLIENT contacts)
    child_first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    child_last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    other_parent_first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    other_parent_last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
