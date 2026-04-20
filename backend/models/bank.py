"""Bank transaction, deposit slip and deposit-payment link models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Column as SAColumn
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base

_Date = date
_Decimal = Decimal


class BankTransactionSource(StrEnum):
    MANUAL = "manual"
    IMPORT = "import"
    SYSTEM_OPENING = "system_opening"


class BankTransactionCategory(StrEnum):
    UNCATEGORIZED = "uncategorized"
    CUSTOMER_PAYMENT = "customer_payment"
    CHEQUE_DEPOSIT = "cheque_deposit"
    CASH_DEPOSIT = "cash_deposit"
    SUPPLIER_PAYMENT = "supplier_payment"
    SALARY = "salary"
    SOCIAL_CHARGE = "social_charge"
    BANK_FEE = "bank_fee"
    INTERNAL_TRANSFER = "internal_transfer"
    GRANT = "grant"
    SEPA_DEBIT = "sepa_debit"
    OTHER_CREDIT = "other_credit"
    OTHER_DEBIT = "other_debit"


class DepositType(StrEnum):
    CHEQUES = "cheques"
    ESPECES = "especes"


# Association table: deposit ↔ payments
deposit_payments = Table(
    "deposit_payments",
    Base.metadata,
    SAColumn("deposit_id", ForeignKey("deposits.id"), primary_key=True),
    SAColumn("payment_id", ForeignKey("payments.id"), primary_key=True),
)


# Association table: bank transaction ↔ payments
bank_transaction_payments = Table(
    "bank_transaction_payments",
    Base.metadata,
    SAColumn("transaction_id", ForeignKey("bank_transactions.id"), primary_key=True),
    SAColumn("payment_id", ForeignKey("payments.id"), primary_key=True),
)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[_Date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[_Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    balance_after: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    reconciled: Mapped[bool] = mapped_column(nullable=False, default=False)
    reconciled_with: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[BankTransactionSource] = mapped_column(
        String(10), nullable=False, default=BankTransactionSource.MANUAL
    )
    detected_category: Mapped[BankTransactionCategory] = mapped_column(
        String(30), nullable=False, default=BankTransactionCategory.UNCATEGORIZED, index=True
    )
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    @property
    def is_system_opening(self) -> bool:
        return self.source == BankTransactionSource.SYSTEM_OPENING


class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[_Date] = mapped_column(Date, nullable=False, index=True)
    type: Mapped[DepositType] = mapped_column(String(10), nullable=False, index=True)
    total_amount: Mapped[_Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    bank_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
