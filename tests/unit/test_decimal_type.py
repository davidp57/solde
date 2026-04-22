"""Unit tests for the DecimalType TypeDecorator (BL-057)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.types import DecimalType

# ---------------------------------------------------------------------------
# Pure unit tests (no DB needed)
# ---------------------------------------------------------------------------


def test_process_result_float_returns_decimal() -> None:
    col_type = DecimalType(10, 2)
    result = col_type.process_result_value(1.23456, dialect=None)  # type: ignore[arg-type]
    assert isinstance(result, Decimal)
    assert result == Decimal("1.23456")


def test_process_result_none_returns_none() -> None:
    col_type = DecimalType(10, 2)
    result = col_type.process_result_value(None, dialect=None)  # type: ignore[arg-type]
    assert result is None


def test_process_result_decimal_returns_decimal_unchanged() -> None:
    col_type = DecimalType(10, 2)
    value = Decimal("9.99")
    result = col_type.process_result_value(value, dialect=None)  # type: ignore[arg-type]
    assert isinstance(result, Decimal)
    assert result == value


def test_process_result_int_returns_decimal() -> None:
    col_type = DecimalType(10, 2)
    result = col_type.process_result_value(100, dialect=None)  # type: ignore[arg-type]
    assert isinstance(result, Decimal)
    assert result == Decimal("100")


# ---------------------------------------------------------------------------
# Integration test: column actually returns Decimal from SQLite
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_decimal_type_column_returns_decimal_from_db(db_session: AsyncSession) -> None:
    """Payment.amount (DecimalType) must return Decimal, never float, after DB round-trip."""
    import datetime

    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
    from backend.models.payment import Payment, PaymentMethod
    from backend.schemas.payment import PaymentCreate
    from backend.services import payment as payment_service

    contact = Contact(
        nom="User",
        prenom="Test",
        type=ContactType.CLIENT,
    )
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="TEST-001",
        contact_id=contact.id,
        type=InvoiceType.CLIENT,
        status=InvoiceStatus.SENT,
        date=datetime.date(2024, 1, 1),
        total_amount=Decimal("99.99"),
        paid_amount=Decimal("0"),
    )
    db_session.add(invoice)
    await db_session.flush()

    created = await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=invoice.id,
            contact_id=contact.id,
            amount=Decimal("99.99"),
            date=datetime.date(2024, 3, 1),
            method=PaymentMethod.CHEQUE,
        ),
    )

    # Reload the raw ORM object directly (bypassing service DTO)
    result = await db_session.execute(select(Payment).where(Payment.id == created.id))
    payment_orm = result.scalar_one()

    assert isinstance(payment_orm.amount, Decimal), (
        f"Expected Decimal, got {type(payment_orm.amount)}: {payment_orm.amount!r}"
    )
