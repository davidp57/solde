"""Integration tests for BL-059: bounded pagination on all list endpoints."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank import BankTransaction
from backend.models.contact import Contact, ContactType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType


class TestDefaultLimitIs100:
    """Verify that list endpoints return at most 100 items when limit is omitted."""

    @pytest.mark.asyncio
    async def test_bank_transactions_default_limit(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ) -> None:
        from datetime import date

        db_session.add_all(
            [
                BankTransaction(
                    date=date(2024, 1, 1),
                    amount=Decimal("10.00"),
                    balance_after=Decimal("10.00"),
                )
                for _ in range(101)
            ]
        )
        await db_session.commit()

        response = await client.get("/api/bank/transactions", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 100

    @pytest.mark.asyncio
    async def test_invoices_default_limit(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ) -> None:
        contact = Contact(type=ContactType.CLIENT, nom="Test")
        db_session.add(contact)
        await db_session.flush()
        from datetime import date

        db_session.add_all(
            [
                Invoice(
                    number=f"2024-{i:04d}",
                    type=InvoiceType.CLIENT,
                    contact_id=contact.id,
                    date=date(2024, 1, 1),
                    total_amount=Decimal("100.00"),
                    paid_amount=Decimal("0.00"),
                    status=InvoiceStatus.SENT,
                )
                for i in range(1, 102)
            ]
        )
        await db_session.commit()

        response = await client.get("/api/invoices/", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 100


class TestLimitParamValidation:
    """Verify that limit > 1000 is rejected and limit = 1000 is accepted."""

    @pytest.mark.asyncio
    async def test_bank_transactions_limit_above_1000_is_rejected(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        response = await client.get("/api/bank/transactions?limit=1001", headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invoices_limit_above_1000_is_rejected(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        response = await client.get("/api/invoices/?limit=1001", headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_1000_is_accepted(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        response = await client.get("/api/invoices/?limit=1000", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_limit_0_is_rejected(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        response = await client.get("/api/invoices/?limit=0", headers=auth_headers)
        assert response.status_code == 422
