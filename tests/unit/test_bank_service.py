"""Unit tests for the bank service — transactions, deposits, balance."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank import BankTransactionSource, DepositType, bank_transaction_payments
from backend.models.contact import Contact, ContactType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.bank import (
    BankTransactionClientPaymentAllocation,
    BankTransactionClientPaymentsCreate,
    BankTransactionCreate,
    BankTransactionUpdate,
    DepositCreate,
)
from backend.services import bank_service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_payment(db: AsyncSession) -> Payment:
    contact = Contact(type=ContactType.CLIENT, nom="Martin")
    db.add(contact)
    await db.flush()

    inv = Invoice(
        number="F-2024-001",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 1, 15),
        total_amount=Decimal("100.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db.add(inv)
    await db.flush()

    payment = Payment(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("100.00"),
        date=date(2024, 2, 1),
        method=PaymentMethod.CHEQUE,
        deposited=False,
    )
    db.add(payment)
    await db.flush()
    return payment


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_transaction(db_session: AsyncSession) -> None:
    payload = BankTransactionCreate(
        date=date(2024, 3, 1),
        amount=Decimal("500.00"),
        description="Virement reçu",
        balance_after=Decimal("1500.00"),
    )
    tx = await bank_service.add_transaction(db_session, payload)

    assert tx.id is not None
    assert tx.amount == Decimal("500.00")
    assert tx.reconciled is False
    assert tx.source == BankTransactionSource.MANUAL


@pytest.mark.asyncio
async def test_get_transaction_not_found(db_session: AsyncSession) -> None:
    result = await bank_service.get_transaction(db_session, 9999)
    assert result is None


@pytest.mark.asyncio
async def test_list_transactions(db_session: AsyncSession) -> None:
    for i in range(3):
        await bank_service.add_transaction(
            db_session,
            BankTransactionCreate(
                date=date(2024, 1, i + 1),
                amount=Decimal("100.00"),
            ),
        )
    txs = await bank_service.list_transactions(db_session)
    assert len(txs) == 3


@pytest.mark.asyncio
async def test_list_transactions_filter_by_date_range(db_session: AsyncSession) -> None:
    await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 7, 31), amount=Decimal("50.00")),
    )
    kept = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 8, 1), amount=Decimal("100.00")),
    )

    txs = await bank_service.list_transactions(
        db_session,
        from_date=date(2024, 8, 1),
        to_date=date(2025, 7, 31),
        limit=None,
    )

    assert [tx.id for tx in txs] == [kept.id]


@pytest.mark.asyncio
async def test_list_transactions_unreconciled_only(db_session: AsyncSession) -> None:
    t1 = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 1), amount=Decimal("100.00")),
    )
    await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 2), amount=Decimal("200.00")),
    )
    # manually reconcile t1
    t1.reconciled = True
    await db_session.commit()

    unreconciled = await bank_service.list_transactions(db_session, unreconciled_only=True)
    assert all(not t.reconciled for t in unreconciled)
    assert len(unreconciled) == 1


@pytest.mark.asyncio
async def test_update_transaction_reconcile(db_session: AsyncSession) -> None:
    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 1), amount=Decimal("100.00")),
    )
    updated = await bank_service.update_transaction(
        db_session, tx, BankTransactionUpdate(reconciled=True, reconciled_with="REF123")
    )
    assert updated.reconciled is True
    assert updated.reconciled_with == "REF123"


@pytest.mark.asyncio
async def test_create_client_payment_from_transaction(db_session: AsyncSession) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Durand")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="F-2024-200",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("120.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(invoice)
    await db_session.flush()

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("120.00"),
            description="VIR DURAND",
            reference="BANK-REF-001",
            source=BankTransactionSource.IMPORT,
        ),
    )

    updated_tx = await bank_service.create_client_payment_from_transaction(
        db_session,
        tx_id=tx.id,
        invoice_id=invoice.id,
    )

    assert updated_tx.reconciled is True
    assert updated_tx.reconciled_with == invoice.number
    assert updated_tx.payment_id is not None

    payment = await db_session.get(Payment, updated_tx.payment_id)
    assert payment is not None
    assert payment.method == PaymentMethod.VIREMENT
    assert payment.reference == "BANK-REF-001"
    assert payment.deposited is True
    assert payment.deposit_date == date(2024, 3, 10)


@pytest.mark.asyncio
async def test_create_client_payments_from_transaction(db_session: AsyncSession) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Durand")
    db_session.add(contact)
    await db_session.flush()

    invoice_one = Invoice(
        number="F-2024-210",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("70.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    invoice_two = Invoice(
        number="F-2024-211",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 2),
        total_amount=Decimal("50.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add_all([invoice_one, invoice_two])
    await db_session.flush()

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("120.00"),
            description="VIR DURAND GROUPE",
            reference="BANK-REF-002",
            source=BankTransactionSource.IMPORT,
        ),
    )

    updated_tx = await bank_service.create_client_payments_from_transaction(
        db_session,
        tx_id=tx.id,
        payload=BankTransactionClientPaymentsCreate(
            allocations=[
                BankTransactionClientPaymentAllocation(
                    invoice_id=invoice_one.id,
                    amount=Decimal("70.00"),
                ),
                BankTransactionClientPaymentAllocation(
                    invoice_id=invoice_two.id,
                    amount=Decimal("50.00"),
                ),
            ]
        ),
    )

    assert updated_tx.reconciled is True
    assert updated_tx.payment_id is None

    payment_ids = await bank_service.get_transaction_payment_ids(db_session, updated_tx.id)
    assert len(payment_ids) == 2

    created_payments = [await db_session.get(Payment, payment_id) for payment_id in payment_ids]
    assert [payment.invoice_id for payment in created_payments if payment is not None] == [
        invoice_one.id,
        invoice_two.id,
    ]
    assert all(
        payment is not None and payment.method == PaymentMethod.VIREMENT
        for payment in created_payments
    )

    await db_session.refresh(invoice_one)
    await db_session.refresh(invoice_two)
    assert invoice_one.status == InvoiceStatus.PAID
    assert invoice_two.status == InvoiceStatus.PAID


@pytest.mark.asyncio
async def test_create_client_payments_from_transaction_rejects_amount_mismatch(
    db_session: AsyncSession,
) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Durand")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="F-2024-212",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("120.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(invoice)
    await db_session.flush()

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("120.00"),
            description="VIR DURAND GROUPE",
            source=BankTransactionSource.IMPORT,
        ),
    )

    with pytest.raises(ValueError, match="allocated amount must match bank transaction amount"):
        await bank_service.create_client_payments_from_transaction(
            db_session,
            tx_id=tx.id,
            payload=BankTransactionClientPaymentsCreate(
                allocations=[
                    BankTransactionClientPaymentAllocation(
                        invoice_id=invoice.id,
                        amount=Decimal("100.00"),
                    )
                ]
            ),
        )


@pytest.mark.asyncio
async def test_create_client_payment_rejects_transaction_with_existing_association_link(
    db_session: AsyncSession,
) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Durand")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="F-2024-216",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("120.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    linked_invoice = Invoice(
        number="F-2024-217",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 2),
        total_amount=Decimal("120.00"),
        paid_amount=Decimal("120.00"),
        status=InvoiceStatus.PAID,
    )
    db_session.add_all([invoice, linked_invoice])
    await db_session.flush()

    linked_payment = Payment(
        invoice_id=linked_invoice.id,
        contact_id=contact.id,
        amount=Decimal("120.00"),
        date=date(2024, 3, 9),
        method=PaymentMethod.VIREMENT,
        deposited=False,
    )
    db_session.add(linked_payment)
    await db_session.flush()

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("120.00"),
            description="VIR DURAND",
            source=BankTransactionSource.IMPORT,
        ),
    )
    tx.reconciled = False
    tx.payment_id = None
    await db_session.flush()
    await db_session.execute(
        insert(bank_transaction_payments),
        [{"transaction_id": tx.id, "payment_id": linked_payment.id}],
    )
    await db_session.commit()

    with pytest.raises(ValueError, match="bank transaction is already reconciled"):
        await bank_service.create_client_payment_from_transaction(
            db_session,
            tx_id=tx.id,
            invoice_id=invoice.id,
        )


@pytest.mark.asyncio
async def test_link_existing_client_payment_to_transaction(db_session: AsyncSession) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Durand")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="F-2024-201",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("120.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(invoice)
    await db_session.flush()

    payment = Payment(
        invoice_id=invoice.id,
        contact_id=contact.id,
        amount=Decimal("120.00"),
        date=date(2024, 3, 9),
        method=PaymentMethod.VIREMENT,
        deposited=False,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("120.00"),
            description="VIR DURAND",
            source=BankTransactionSource.IMPORT,
        ),
    )

    updated_tx = await bank_service.link_client_payment_to_transaction(
        db_session,
        tx_id=tx.id,
        payment_id=payment.id,
    )

    assert updated_tx.reconciled is True
    assert updated_tx.payment_id == payment.id

    await db_session.refresh(payment)
    assert payment.deposited is True
    assert payment.deposit_date == date(2024, 3, 10)


@pytest.mark.asyncio
async def test_link_existing_client_payments_to_transaction(db_session: AsyncSession) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Durand")
    db_session.add(contact)
    await db_session.flush()

    invoice_one = Invoice(
        number="F-2024-213",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("70.00"),
        paid_amount=Decimal("70.00"),
        status=InvoiceStatus.PAID,
    )
    invoice_two = Invoice(
        number="F-2024-214",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 2),
        total_amount=Decimal("50.00"),
        paid_amount=Decimal("50.00"),
        status=InvoiceStatus.PAID,
    )
    db_session.add_all([invoice_one, invoice_two])
    await db_session.flush()

    payment_one = Payment(
        invoice_id=invoice_one.id,
        contact_id=contact.id,
        amount=Decimal("70.00"),
        date=date(2024, 3, 8),
        method=PaymentMethod.VIREMENT,
        reference="LEGACY-VIR-070",
        deposited=False,
    )
    payment_two = Payment(
        invoice_id=invoice_two.id,
        contact_id=contact.id,
        amount=Decimal("50.00"),
        date=date(2024, 3, 9),
        method=PaymentMethod.VIREMENT,
        reference="LEGACY-VIR-050",
        deposited=False,
    )
    db_session.add_all([payment_one, payment_two])
    await db_session.commit()
    await db_session.refresh(payment_one)
    await db_session.refresh(payment_two)

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("120.00"),
            description="VIR DURAND GROUPE",
            source=BankTransactionSource.IMPORT,
        ),
    )

    updated_tx = await bank_service.link_client_payments_to_transaction(
        db_session,
        tx_id=tx.id,
        payment_ids=[payment_one.id, payment_two.id],
    )

    assert updated_tx.reconciled is True
    assert updated_tx.payment_id is None

    payment_ids = await bank_service.get_transaction_payment_ids(db_session, updated_tx.id)
    assert payment_ids == [payment_one.id, payment_two.id]

    await db_session.refresh(payment_one)
    await db_session.refresh(payment_two)
    assert payment_one.deposited is True
    assert payment_two.deposited is True
    assert payment_one.deposit_date == date(2024, 3, 10)
    assert payment_two.deposit_date == date(2024, 3, 10)


@pytest.mark.asyncio
async def test_get_transaction_payment_ids_map_supports_association_and_legacy_link(
    db_session: AsyncSession,
) -> None:
    payment = await _make_payment(db_session)
    second_payment = Payment(
        invoice_id=payment.invoice_id,
        contact_id=payment.contact_id,
        amount=Decimal("40.00"),
        date=date(2024, 2, 2),
        method=PaymentMethod.CHEQUE,
        deposited=False,
    )
    db_session.add(second_payment)
    await db_session.flush()

    legacy_tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 3, 10), amount=Decimal("100.00")),
    )
    legacy_tx.payment_id = payment.id
    associated_tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 3, 11), amount=Decimal("40.00")),
    )
    await db_session.execute(
        insert(bank_transaction_payments),
        [{"transaction_id": associated_tx.id, "payment_id": second_payment.id}],
    )
    await db_session.commit()

    payment_ids_by_tx_id = await bank_service.get_transaction_payment_ids_map(
        db_session,
        [legacy_tx.id, associated_tx.id],
    )

    assert payment_ids_by_tx_id == {
        legacy_tx.id: [payment.id],
        associated_tx.id: [second_payment.id],
    }


@pytest.mark.asyncio
async def test_link_existing_client_payments_rejects_amount_mismatch(
    db_session: AsyncSession,
) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Durand")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="F-2024-215",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("120.00"),
        paid_amount=Decimal("120.00"),
        status=InvoiceStatus.PAID,
    )
    db_session.add(invoice)
    await db_session.flush()

    payment = Payment(
        invoice_id=invoice.id,
        contact_id=contact.id,
        amount=Decimal("100.00"),
        date=date(2024, 3, 8),
        method=PaymentMethod.VIREMENT,
        deposited=False,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("120.00"),
            description="VIR DURAND GROUPE",
            source=BankTransactionSource.IMPORT,
        ),
    )

    with pytest.raises(
        ValueError,
        match="linked payments total must match bank transaction amount",
    ):
        await bank_service.link_client_payments_to_transaction(
            db_session,
            tx_id=tx.id,
            payment_ids=[payment.id],
        )


@pytest.mark.asyncio
async def test_create_supplier_payment_from_transaction(db_session: AsyncSession) -> None:
    contact = Contact(type=ContactType.FOURNISSEUR, nom="Fournisseur")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="A-2024-200",
        type=InvoiceType.FOURNISSEUR,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("220.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
        reference="SUP-001",
    )
    db_session.add(invoice)
    await db_session.flush()

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("-220.00"),
            description="VIR FOURNISSEUR",
            reference="SUP-001",
            source=BankTransactionSource.IMPORT,
        ),
    )

    updated_tx = await bank_service.create_supplier_payment_from_transaction(
        db_session,
        tx_id=tx.id,
        invoice_id=invoice.id,
    )

    assert updated_tx.reconciled is True
    assert updated_tx.reconciled_with == invoice.number
    assert updated_tx.payment_id is not None

    payment = await db_session.get(Payment, updated_tx.payment_id)
    assert payment is not None
    assert payment.amount == Decimal("220.00")
    assert payment.method == PaymentMethod.VIREMENT
    assert payment.deposited is True
    assert payment.deposit_date == date(2024, 3, 10)


@pytest.mark.asyncio
async def test_link_existing_supplier_payment_to_transaction(db_session: AsyncSession) -> None:
    contact = Contact(type=ContactType.FOURNISSEUR, nom="Fournisseur")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number="A-2024-201",
        type=InvoiceType.FOURNISSEUR,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("220.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(invoice)
    await db_session.flush()

    payment = Payment(
        invoice_id=invoice.id,
        contact_id=contact.id,
        amount=Decimal("220.00"),
        date=date(2024, 3, 9),
        method=PaymentMethod.VIREMENT,
        deposited=False,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)

    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(
            date=date(2024, 3, 10),
            amount=Decimal("-220.00"),
            description="VIR FOURNISSEUR",
            source=BankTransactionSource.IMPORT,
        ),
    )

    updated_tx = await bank_service.link_supplier_payment_to_transaction(
        db_session,
        tx_id=tx.id,
        payment_id=payment.id,
    )

    assert updated_tx.reconciled is True
    assert updated_tx.payment_id == payment.id

    await db_session.refresh(payment)
    assert payment.deposited is True
    assert payment.deposit_date == date(2024, 3, 10)


@pytest.mark.asyncio
async def test_get_bank_balance(db_session: AsyncSession) -> None:
    await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 1), amount=Decimal("500.00")),
    )
    await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 2), amount=Decimal("-100.00")),
    )
    balance = await bank_service.get_bank_balance(db_session)
    assert balance == Decimal("400.00")


# ---------------------------------------------------------------------------
# Deposits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_deposit_marks_payments_deposited(
    db_session: AsyncSession,
) -> None:
    p = await _make_payment(db_session)
    payload = DepositCreate(
        date=date(2024, 3, 1),
        type=DepositType.CHEQUES,
        payment_ids=[p.id],
        bank_reference="BDX-001",
    )
    deposit = await bank_service.create_deposit(db_session, payload)

    assert deposit.id is not None
    assert deposit.total_amount == Decimal("100.00")

    await db_session.refresh(p)
    assert p.deposited is True
    assert p.deposit_date == date(2024, 3, 1)


@pytest.mark.asyncio
async def test_create_deposit_invalid_payment_raises(db_session: AsyncSession) -> None:
    payload = DepositCreate(
        date=date(2024, 3, 1),
        type=DepositType.CHEQUES,
        payment_ids=[99999],
    )
    with pytest.raises(ValueError, match="not found"):
        await bank_service.create_deposit(db_session, payload)


@pytest.mark.asyncio
async def test_get_deposit_payment_ids(db_session: AsyncSession) -> None:
    p = await _make_payment(db_session)
    deposit = await bank_service.create_deposit(
        db_session,
        DepositCreate(
            date=date(2024, 3, 1),
            type=DepositType.CHEQUES,
            payment_ids=[p.id],
        ),
    )
    ids = await bank_service.get_deposit_payment_ids(db_session, deposit.id)
    assert ids == [p.id]


@pytest.mark.asyncio
async def test_list_deposits(db_session: AsyncSession) -> None:
    p1 = await _make_payment(db_session)

    contact = await db_session.get(Contact, p1.contact_id)
    assert contact is not None
    inv = await db_session.get(Invoice, p1.invoice_id)
    assert inv is not None
    p2 = Payment(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("50.00"),
        date=date(2024, 2, 2),
        method=PaymentMethod.ESPECES,
        deposited=False,
    )
    db_session.add(p2)
    await db_session.flush()

    await bank_service.create_deposit(
        db_session,
        DepositCreate(date=date(2024, 3, 1), type=DepositType.CHEQUES, payment_ids=[p1.id]),
    )
    await bank_service.create_deposit(
        db_session,
        DepositCreate(date=date(2024, 3, 2), type=DepositType.ESPECES, payment_ids=[p2.id]),
    )

    deposits = await bank_service.list_deposits(db_session)
    assert len(deposits) == 2


@pytest.mark.asyncio
async def test_list_deposits_filter_by_date_range(db_session: AsyncSession) -> None:
    p1 = await _make_payment(db_session)
    await bank_service.create_deposit(
        db_session,
        DepositCreate(date=date(2024, 7, 31), type=DepositType.CHEQUES, payment_ids=[p1.id]),
    )

    contact = await db_session.get(Contact, p1.contact_id)
    assert contact is not None
    inv = await db_session.get(Invoice, p1.invoice_id)
    assert inv is not None
    p2 = Payment(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("80.00"),
        date=date(2024, 8, 2),
        method=PaymentMethod.CHEQUE,
        deposited=False,
    )
    db_session.add(p2)
    await db_session.flush()
    kept = await bank_service.create_deposit(
        db_session,
        DepositCreate(date=date(2024, 8, 3), type=DepositType.CHEQUES, payment_ids=[p2.id]),
    )

    deposits = await bank_service.list_deposits(
        db_session,
        from_date=date(2024, 8, 1),
        to_date=date(2025, 7, 31),
        limit=None,
    )

    assert [deposit.id for deposit in deposits] == [kept.id]
