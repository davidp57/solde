"""Accounting rules and rule entries — configurable double-entry generation."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class TriggerType(StrEnum):
    INVOICE_CLIENT_CS = "invoice_client_cs"
    INVOICE_CLIENT_A = "invoice_client_a"
    INVOICE_CLIENT_CS_A = "invoice_client_cs_a"
    INVOICE_CLIENT_GENERAL = "invoice_client_general"
    INVOICE_FOURNISSEUR_SUBCONTRACTING = "invoice_fournisseur_subcontracting"
    INVOICE_FOURNISSEUR_GENERAL = "invoice_fournisseur_general"
    PAYMENT_RECEIVED_ESPECES = "payment_received_especes"
    PAYMENT_RECEIVED_CHEQUE = "payment_received_cheque"
    PAYMENT_RECEIVED_VIREMENT = "payment_received_virement"
    PAYMENT_SENT_VIREMENT = "payment_sent_virement"
    DEPOSIT_ESPECES = "deposit_especes"
    DEPOSIT_CHEQUES = "deposit_cheques"
    BANK_FEES = "bank_fees"
    SALARY_GROSS = "salary_gross"
    SALARY_EMPLOYER_CHARGES = "salary_employer_charges"
    SALARY_PAYMENT = "salary_payment"
    MANUAL = "manual"


class EntrySide(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class AccountingRule(Base):
    """A named rule that generates accounting entries when its trigger fires."""

    __tablename__ = "accounting_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    trigger_type: Mapped[TriggerType] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    entries: Mapped[list[AccountingRuleEntry]] = relationship(
        "AccountingRuleEntry",
        back_populates="rule",
        cascade="all, delete-orphan",
        order_by="AccountingRuleEntry.id",
    )


class AccountingRuleEntry(Base):
    """One debit or credit line within a rule."""

    __tablename__ = "accounting_rule_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rule_id: Mapped[int] = mapped_column(
        ForeignKey("accounting_rules.id"), nullable=False, index=True
    )
    account_number: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[EntrySide] = mapped_column(String(10), nullable=False)
    # Jinja2 template for the entry label — context vars: amount, date, etc.
    description_template: Mapped[str] = mapped_column(
        String(500), nullable=False, default="{{label}}"
    )

    rule: Mapped[AccountingRule] = relationship("AccountingRule", back_populates="entries")


# ---------------------------------------------------------------------------
# Default rules seeded from plan.md
# ---------------------------------------------------------------------------

DEFAULT_RULES: list[dict[str, object]] = [
    {
        "name": "Facture client — cours de soutien",
        "trigger_type": TriggerType.INVOICE_CLIENT_CS,
        "description": "411100 D / 706110 C",
        "entries": [
            {
                "account_number": "411100",
                "side": EntrySide.DEBIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
            {
                "account_number": "706110",
                "side": EntrySide.CREDIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
        ],
    },
    {
        "name": "Facture client — adhésion",
        "trigger_type": TriggerType.INVOICE_CLIENT_A,
        "description": "411100 D / 756000 C",
        "entries": [
            {
                "account_number": "411100",
                "side": EntrySide.DEBIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
            {
                "account_number": "756000",
                "side": EntrySide.CREDIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
        ],
    },
    {
        "name": "Facture client — cours + adhésion",
        "trigger_type": TriggerType.INVOICE_CLIENT_CS_A,
        "description": "411100 D / 706110 C",
        "entries": [
            {
                "account_number": "411100",
                "side": EntrySide.DEBIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
            {
                "account_number": "706110",
                "side": EntrySide.CREDIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
        ],
    },
    {
        "name": "Facture client — général",
        "trigger_type": TriggerType.INVOICE_CLIENT_GENERAL,
        "description": "411100 D / 758000 C",
        "entries": [
            {
                "account_number": "411100",
                "side": EntrySide.DEBIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
            {
                "account_number": "758000",
                "side": EntrySide.CREDIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
        ],
    },
    {
        "name": "Facture fournisseur — sous-traitance",
        "trigger_type": TriggerType.INVOICE_FOURNISSEUR_SUBCONTRACTING,
        "description": "611100 D / 401000 C",
        "entries": [
            {
                "account_number": "611100",
                "side": EntrySide.DEBIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
            {
                "account_number": "401000",
                "side": EntrySide.CREDIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
        ],
    },
    {
        "name": "Facture fournisseur — général",
        "trigger_type": TriggerType.INVOICE_FOURNISSEUR_GENERAL,
        "description": "602250 D / 401000 C",
        "entries": [
            {
                "account_number": "602250",
                "side": EntrySide.DEBIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
            {
                "account_number": "401000",
                "side": EntrySide.CREDIT,
                "description_template": "Fact. {{number}} {{contact}}",
            },
        ],
    },
    {
        "name": "Paiement reçu — espèces",
        "trigger_type": TriggerType.PAYMENT_RECEIVED_ESPECES,
        "description": "531000 D / 411100 C",
        "entries": [
            {
                "account_number": "531000",
                "side": EntrySide.DEBIT,
                "description_template": "Règt. {{label}}",
            },
            {
                "account_number": "411100",
                "side": EntrySide.CREDIT,
                "description_template": "Règt. {{label}}",
            },
        ],
    },
    {
        "name": "Paiement reçu — chèque",
        "trigger_type": TriggerType.PAYMENT_RECEIVED_CHEQUE,
        "description": "511200 D / 411100 C",
        "entries": [
            {
                "account_number": "511200",
                "side": EntrySide.DEBIT,
                "description_template": "Règt. {{label}}",
            },
            {
                "account_number": "411100",
                "side": EntrySide.CREDIT,
                "description_template": "Règt. {{label}}",
            },
        ],
    },
    {
        "name": "Paiement reçu — virement",
        "trigger_type": TriggerType.PAYMENT_RECEIVED_VIREMENT,
        "description": "512100 D / 411100 C",
        "entries": [
            {
                "account_number": "512100",
                "side": EntrySide.DEBIT,
                "description_template": "Règt. {{label}}",
            },
            {
                "account_number": "411100",
                "side": EntrySide.CREDIT,
                "description_template": "Règt. {{label}}",
            },
        ],
    },
    {
        "name": "Paiement envoyé — virement fournisseur",
        "trigger_type": TriggerType.PAYMENT_SENT_VIREMENT,
        "description": "401000 D / 512100 C",
        "entries": [
            {
                "account_number": "401000",
                "side": EntrySide.DEBIT,
                "description_template": "Règt. {{label}}",
            },
            {
                "account_number": "512100",
                "side": EntrySide.CREDIT,
                "description_template": "Règt. {{label}}",
            },
        ],
    },
    {
        "name": "Remise en banque — espèces",
        "trigger_type": TriggerType.DEPOSIT_ESPECES,
        "description": "512100 D / 531000 C",
        "entries": [
            {
                "account_number": "512100",
                "side": EntrySide.DEBIT,
                "description_template": "Remise espèces {{date}}",
            },
            {
                "account_number": "531000",
                "side": EntrySide.CREDIT,
                "description_template": "Remise espèces {{date}}",
            },
        ],
    },
    {
        "name": "Remise en banque — chèques",
        "trigger_type": TriggerType.DEPOSIT_CHEQUES,
        "description": "512100 D / 511200 C",
        "entries": [
            {
                "account_number": "512100",
                "side": EntrySide.DEBIT,
                "description_template": "Remise chèques {{date}}",
            },
            {
                "account_number": "511200",
                "side": EntrySide.CREDIT,
                "description_template": "Remise chèques {{date}}",
            },
        ],
    },
    {
        "name": "Frais bancaires",
        "trigger_type": TriggerType.BANK_FEES,
        "description": "627000 D / 512100 C",
        "entries": [
            {
                "account_number": "627000",
                "side": EntrySide.DEBIT,
                "description_template": "Frais bancaires {{date}}",
            },
            {
                "account_number": "512100",
                "side": EntrySide.CREDIT,
                "description_template": "Frais bancaires {{date}}",
            },
        ],
    },
    {
        "name": "Salaire brut — charge",
        "trigger_type": TriggerType.SALARY_GROSS,
        "description": "641000 D / 421000 C",
        "entries": [
            {
                "account_number": "641000",
                "side": EntrySide.DEBIT,
                "description_template": "Salaire {{employee}} {{month}}",
            },
            {
                "account_number": "421000",
                "side": EntrySide.CREDIT,
                "description_template": "Salaire {{employee}} {{month}}",
            },
        ],
    },
    {
        "name": "Cotisations patronales",
        "trigger_type": TriggerType.SALARY_EMPLOYER_CHARGES,
        "description": "645100 D / 431100 C",
        "entries": [
            {
                "account_number": "645100",
                "side": EntrySide.DEBIT,
                "description_template": "Cotisations {{employee}} {{month}}",
            },
            {
                "account_number": "431100",
                "side": EntrySide.CREDIT,
                "description_template": "Cotisations {{employee}} {{month}}",
            },
        ],
    },
    {
        "name": "Paiement salaire net",
        "trigger_type": TriggerType.SALARY_PAYMENT,
        "description": "421000 D / 512100 C",
        "entries": [
            {
                "account_number": "421000",
                "side": EntrySide.DEBIT,
                "description_template": "Paiement salaire {{employee}} {{month}}",
            },
            {
                "account_number": "512100",
                "side": EntrySide.CREDIT,
                "description_template": "Paiement salaire {{employee}} {{month}}",
            },
        ],
    },
]
