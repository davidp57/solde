"""Salary model — monthly salary records linked to employee contacts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.models.types import DecimalType

if TYPE_CHECKING:
    from backend.models.contact import Contact

_Decimal = Decimal


class Salary(Base):
    """Monthly salary record for one employee (data sourced from CEA platform)."""

    __tablename__ = "salaries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Employee — linked to a contact of type fournisseur or client
    employee_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False, index=True)

    # Period in YYYY-MM format (e.g. "2024-09")
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)

    # Hours worked this month
    hours: Mapped[_Decimal] = mapped_column(DecimalType(8, 2), nullable=False, default=Decimal("0"))

    # Gross salary (salaire brut)
    gross: Mapped[_Decimal] = mapped_column(DecimalType(10, 2), nullable=False)

    # Employee social charges (cotisations salariales)
    employee_charges: Mapped[_Decimal] = mapped_column(
        DecimalType(10, 2), nullable=False, default=Decimal("0")
    )

    # Employer social charges (cotisations patronales)
    employer_charges: Mapped[_Decimal] = mapped_column(
        DecimalType(10, 2), nullable=False, default=Decimal("0")
    )

    # Income tax withheld at source (prélèvement à la source)
    tax: Mapped[_Decimal] = mapped_column(DecimalType(10, 2), nullable=False, default=Decimal("0"))

    # Net salary paid to employee
    net_pay: Mapped[_Decimal] = mapped_column(DecimalType(10, 2), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationship
    employee: Mapped[Contact] = relationship("Contact", lazy="select")

    @property
    def total_cost(self) -> _Decimal:
        """Total employer cost = gross + employer_charges."""
        return self.gross + self.employer_charges
