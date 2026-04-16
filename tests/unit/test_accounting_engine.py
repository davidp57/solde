"""Unit tests for the accounting engine service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.accounting_entry import EntrySourceType
from backend.models.accounting_rule import (
    DEFAULT_RULES,
    AccountingRule,
    AccountingRuleEntry,
    EntrySide,
    TriggerType,
)
from backend.models.bank import Deposit, DepositType
from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.invoice import Invoice, InvoiceLabel, InvoiceLine, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.models.salary import Salary
from backend.services.accounting_engine import (
    _render_template,
    generate_entries_for_deposit,
    generate_entries_for_invoice,
    generate_entries_for_payment,
    generate_entries_for_salary,
    seed_default_rules,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_one_rule(
    db: AsyncSession,
    trigger: TriggerType,
    debit_account: str,
    credit_account: str,
) -> AccountingRule:
    """Insert a minimal two-line rule for a given trigger."""
    rule = AccountingRule(
        name=f"Test rule {trigger}",
        trigger_type=trigger,
        is_active=True,
        priority=10,
    )
    db.add(rule)
    await db.flush()
    db.add(
        AccountingRuleEntry(
            rule_id=rule.id,
            account_number=debit_account,
            side=EntrySide.DEBIT,
            description_template="{{label}}",
        )
    )
    db.add(
        AccountingRuleEntry(
            rule_id=rule.id,
            account_number=credit_account,
            side=EntrySide.CREDIT,
            description_template="{{label}}",
        )
    )
    await db.commit()
    await db.refresh(rule)
    return rule


async def _make_invoice(
    db: AsyncSession,
    *,
    inv_type: InvoiceType = InvoiceType.CLIENT,
    label: InvoiceLabel | None = InvoiceLabel.CS,
    total: Decimal = Decimal("100.00"),
    lines: list[tuple[str, Decimal]] | None = None,
    has_explicit_breakdown: bool = False,
) -> Invoice:
    invoice_total = sum((amount for _, amount in lines), Decimal("0")) if lines else total
    inv = Invoice(
        number="2024-C-0001",
        type=inv_type,
        contact_id=1,
        date=date(2024, 1, 15),
        total_amount=invoice_total,
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
        label=label,
        has_explicit_breakdown=has_explicit_breakdown,
    )
    db.add(inv)
    await db.flush()
    for description, amount in lines or []:
        db.add(
            InvoiceLine(
                invoice_id=inv.id,
                description=description,
                quantity=Decimal("1"),
                unit_price=amount,
                amount=amount,
            )
        )
    await db.commit()
    result = await db.execute(
        select(Invoice).where(Invoice.id == inv.id).options(selectinload(Invoice.lines))
    )
    return result.scalar_one()


async def _make_payment(
    db: AsyncSession,
    method: PaymentMethod = PaymentMethod.CHEQUE,
    invoice_id: int = 1,
    amount: Decimal = Decimal("50.00"),
) -> Payment:
    pay = Payment(
        invoice_id=invoice_id,
        contact_id=1,
        date=date(2024, 1, 20),
        amount=amount,
        method=method,
    )
    db.add(pay)
    await db.commit()
    await db.refresh(pay)
    return pay


async def _make_deposit(
    db: AsyncSession,
    dep_type: DepositType = DepositType.CHEQUES,
    total: Decimal = Decimal("200.00"),
) -> Deposit:
    dep = Deposit(
        date=date(2024, 1, 25),
        type=dep_type,
        total_amount=total,
    )
    db.add(dep)
    await db.commit()
    await db.refresh(dep)
    return dep


async def _create_fiscal_year(
    db: AsyncSession,
    *,
    name: str,
    start: date,
    end: date,
) -> FiscalYear:
    fiscal_year = FiscalYear(
        name=name,
        start_date=start,
        end_date=end,
        status=FiscalYearStatus.OPEN,
    )
    db.add(fiscal_year)
    await db.commit()
    await db.refresh(fiscal_year)
    return fiscal_year


async def _make_employee(db: AsyncSession) -> Contact:
    employee = Contact(type=ContactType.FOURNISSEUR, nom="Martin", prenom="Alice")
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return employee


async def _make_salary(db: AsyncSession, employee_id: int) -> Salary:
    salary = Salary(
        employee_id=employee_id,
        month="2024-01",
        hours=Decimal("35.00"),
        gross=Decimal("1000.00"),
        employee_charges=Decimal("220.00"),
        employer_charges=Decimal("420.00"),
        tax=Decimal("80.00"),
        net_pay=Decimal("700.00"),
    )
    db.add(salary)
    await db.commit()
    await db.refresh(salary)
    return salary


# ---------------------------------------------------------------------------
# _render_template
# ---------------------------------------------------------------------------


class TestRenderTemplate:
    def test_no_placeholders(self) -> None:
        assert _render_template("Hello world", {}) == "Hello world"

    def test_simple_substitution(self) -> None:
        result = _render_template("Fact. {{number}}", {"number": "2024-C-0001"})
        assert result == "Fact. 2024-C-0001"

    def test_multiple_placeholders(self) -> None:
        result = _render_template("{{a}} / {{b}}", {"a": "foo", "b": "bar"})
        assert result == "foo / bar"

    def test_missing_key_kept(self) -> None:
        # Unknown keys are left as-is
        result = _render_template("{{unknown}}", {})
        assert result == "{{unknown}}"

    def test_key_without_spaces(self) -> None:
        # Regex matches {{key}} without spaces — spaces in template are literal
        result = _render_template("{{key}}", {"key": "value"})
        assert result == "value"


# ---------------------------------------------------------------------------
# generate_entries_for_invoice
# ---------------------------------------------------------------------------


class TestGenerateEntriesForInvoice:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_rule(self, db_session: AsyncSession) -> None:
        inv = await _make_invoice(db_session)
        entries = await generate_entries_for_invoice(db_session, inv)
        assert entries == []

    @pytest.mark.asyncio
    async def test_client_cs_label(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        inv = await _make_invoice(db_session, label=InvoiceLabel.CS)
        entries = await generate_entries_for_invoice(db_session, inv)
        assert len(entries) == 2
        debit = next(e for e in entries if e.debit > 0)
        credit = next(e for e in entries if e.credit > 0)
        assert debit.account_number == "411100"
        assert credit.account_number == "706110"
        assert debit.debit == Decimal("100.00")
        assert credit.credit == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_assigns_fiscal_year_from_invoice_date(self, db_session: AsyncSession) -> None:
        fiscal_year = await _create_fiscal_year(
            db_session,
            name="2024",
            start=date(2024, 1, 1),
            end=date(2024, 12, 31),
        )
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        inv = await _make_invoice(db_session, label=InvoiceLabel.CS)

        entries = await generate_entries_for_invoice(db_session, inv)

        assert len(entries) == 2
        assert {entry.fiscal_year_id for entry in entries} == {fiscal_year.id}

    @pytest.mark.asyncio
    async def test_client_adhesion_label(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_A, "411100", "756000")
        inv = await _make_invoice(db_session, label=InvoiceLabel.ADHESION)
        entries = await generate_entries_for_invoice(db_session, inv)
        assert len(entries) == 2
        assert any(e.account_number == "756000" for e in entries)

    @pytest.mark.asyncio
    async def test_client_cs_a_label(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS_A, "411100", "706110")
        inv = await _make_invoice(db_session, label=InvoiceLabel.CS_ADHESION)
        entries = await generate_entries_for_invoice(db_session, inv)
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_client_cs_a_lines_split_credit_accounts(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS_A, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_A, "411100", "756000")
        inv = await _make_invoice(
            db_session,
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                ("Cours de soutien", Decimal("130.00")),
                ("Adhesion annuelle", Decimal("30.00")),
            ],
            has_explicit_breakdown=True,
        )

        entries = await generate_entries_for_invoice(db_session, inv)

        assert len(entries) == 3
        debit = next(entry for entry in entries if entry.debit > 0)
        assert debit.account_number == "411100"
        assert debit.debit == Decimal("160.00")
        assert {entry.account_number: entry.credit for entry in entries if entry.credit > 0} == {
            "706110": Decimal("130.00"),
            "756000": Decimal("30.00"),
        }

    @pytest.mark.asyncio
    async def test_client_cs_a_unclassified_lines_fall_back_to_default_rule(
        self, db_session: AsyncSession
    ) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS_A, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_A, "411100", "756000")
        inv = await _make_invoice(
            db_session,
            label=InvoiceLabel.CS_ADHESION,
            lines=[("Pack rentree", Decimal("100.00"))],
        )

        entries = await generate_entries_for_invoice(db_session, inv)

        assert len(entries) == 2
        assert any(
            entry.account_number == "706110" and entry.credit == Decimal("100.00")
            for entry in entries
        )

    @pytest.mark.asyncio
    async def test_client_cs_a_lines_without_explicit_breakdown_fall_back_to_default_rule(
        self, db_session: AsyncSession
    ) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS_A, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_A, "411100", "756000")
        inv = await _make_invoice(
            db_session,
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                ("Cours de soutien", Decimal("130.00")),
                ("Adhesion annuelle", Decimal("30.00")),
            ],
        )

        entries = await generate_entries_for_invoice(db_session, inv)

        assert len(entries) == 2
        assert any(
            entry.account_number == "706110" and entry.credit == Decimal("160.00")
            for entry in entries
        )
        assert all(entry.account_number != "756000" or entry.credit <= 0 for entry in entries)

    @pytest.mark.asyncio
    async def test_client_cs_a_explicit_breakdown_skips_zero_credit_entry(
        self, db_session: AsyncSession
    ) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS_A, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_A, "411100", "756000")
        inv = await _make_invoice(
            db_session,
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                ("Cours de soutien", Decimal("160.00")),
                ("Adhesion annuelle", Decimal("0.00")),
            ],
            has_explicit_breakdown=True,
        )

        entries = await generate_entries_for_invoice(db_session, inv)

        assert len(entries) == 2
        assert any(
            entry.account_number == "411100" and entry.debit == Decimal("160.00")
            for entry in entries
        )
        assert any(
            entry.account_number == "706110" and entry.credit == Decimal("160.00")
            for entry in entries
        )
        assert all(entry.account_number != "756000" for entry in entries)

    @pytest.mark.asyncio
    async def test_client_cs_a_explicit_breakdown_with_zero_component_does_not_require_unused_rule(
        self, db_session: AsyncSession
    ) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS_A, "411100", "706110")
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        inv = await _make_invoice(
            db_session,
            label=InvoiceLabel.CS_ADHESION,
            lines=[
                ("Cours de soutien", Decimal("160.00")),
                ("Adhesion annuelle", Decimal("0.00")),
            ],
            has_explicit_breakdown=True,
        )

        entries = await generate_entries_for_invoice(db_session, inv)

        assert len(entries) == 2
        assert any(
            entry.account_number == "411100" and entry.debit == Decimal("160.00")
            for entry in entries
        )
        assert any(
            entry.account_number == "706110" and entry.credit == Decimal("160.00")
            for entry in entries
        )

    @pytest.mark.asyncio
    async def test_client_general_label(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_GENERAL, "411100", "758000")
        inv = await _make_invoice(db_session, label=InvoiceLabel.GENERAL)
        entries = await generate_entries_for_invoice(db_session, inv)
        assert len(entries) == 2
        assert any(e.account_number == "758000" for e in entries)

    @pytest.mark.asyncio
    async def test_client_no_label_falls_back_to_general(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_GENERAL, "411100", "758000")
        inv = await _make_invoice(db_session, label=None)
        entries = await generate_entries_for_invoice(db_session, inv)
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_fournisseur_cs_triggers_subcontracting(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(
            db_session,
            TriggerType.INVOICE_FOURNISSEUR_SUBCONTRACTING,
            "611100",
            "401000",
        )
        inv = await _make_invoice(
            db_session, inv_type=InvoiceType.FOURNISSEUR, label=InvoiceLabel.CS
        )
        entries = await generate_entries_for_invoice(db_session, inv)
        assert len(entries) == 2
        assert any(e.account_number == "611100" for e in entries)

    @pytest.mark.asyncio
    async def test_fournisseur_general_label(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(
            db_session, TriggerType.INVOICE_FOURNISSEUR_GENERAL, "602250", "401000"
        )
        inv = await _make_invoice(
            db_session, inv_type=InvoiceType.FOURNISSEUR, label=InvoiceLabel.GENERAL
        )
        entries = await generate_entries_for_invoice(db_session, inv)
        assert len(entries) == 2
        assert any(e.account_number == "602250" for e in entries)

    @pytest.mark.asyncio
    async def test_source_type_is_invoice(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        inv = await _make_invoice(db_session)
        entries = await generate_entries_for_invoice(db_session, inv)
        for e in entries:
            assert e.source_type == EntrySourceType.INVOICE
            assert e.source_id == inv.id

    @pytest.mark.asyncio
    async def test_entry_numbers_are_unique(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.INVOICE_CLIENT_CS, "411100", "706110")
        inv = await _make_invoice(db_session)
        entries = await generate_entries_for_invoice(db_session, inv)
        nums = [e.entry_number for e in entries]
        assert len(set(nums)) == len(nums)


# ---------------------------------------------------------------------------
# generate_entries_for_payment
# ---------------------------------------------------------------------------


class TestGenerateEntriesForPayment:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_rule(self, db_session: AsyncSession) -> None:
        inv = await _make_invoice(db_session)
        pay = await _make_payment(db_session, invoice_id=inv.id)
        result = await generate_entries_for_payment(db_session, pay, InvoiceType.CLIENT)
        assert result == []

    @pytest.mark.asyncio
    async def test_payment_received_cheque(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.PAYMENT_RECEIVED_CHEQUE, "511200", "411100")
        inv = await _make_invoice(db_session)
        pay = await _make_payment(db_session, method=PaymentMethod.CHEQUE, invoice_id=inv.id)
        entries = await generate_entries_for_payment(db_session, pay, InvoiceType.CLIENT)
        assert len(entries) == 2
        assert any(e.account_number == "511200" for e in entries)

    @pytest.mark.asyncio
    async def test_payment_received_especes(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.PAYMENT_RECEIVED_ESPECES, "531000", "411100")
        inv = await _make_invoice(db_session)
        pay = await _make_payment(db_session, method=PaymentMethod.ESPECES, invoice_id=inv.id)
        entries = await generate_entries_for_payment(db_session, pay, InvoiceType.CLIENT)
        assert len(entries) == 2
        assert any(e.account_number == "531000" for e in entries)

    @pytest.mark.asyncio
    async def test_payment_received_virement(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.PAYMENT_RECEIVED_VIREMENT, "512100", "411100")
        inv = await _make_invoice(db_session)
        pay = await _make_payment(db_session, method=PaymentMethod.VIREMENT, invoice_id=inv.id)
        entries = await generate_entries_for_payment(db_session, pay, InvoiceType.CLIENT)
        assert len(entries) == 2
        assert any(e.account_number == "512100" for e in entries)

    @pytest.mark.asyncio
    async def test_payment_sent_virement_fournisseur(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.PAYMENT_SENT_VIREMENT, "401000", "512100")
        inv = await _make_invoice(db_session, inv_type=InvoiceType.FOURNISSEUR)
        pay = await _make_payment(db_session, method=PaymentMethod.VIREMENT, invoice_id=inv.id)
        entries = await generate_entries_for_payment(db_session, pay, InvoiceType.FOURNISSEUR)
        assert len(entries) == 2
        assert any(e.account_number == "401000" for e in entries)

    @pytest.mark.asyncio
    async def test_payment_sent_especes_fournisseur(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.PAYMENT_SENT_ESPECES, "401000", "531000")
        inv = await _make_invoice(db_session, inv_type=InvoiceType.FOURNISSEUR)
        pay = await _make_payment(db_session, method=PaymentMethod.ESPECES, invoice_id=inv.id)
        entries = await generate_entries_for_payment(db_session, pay, InvoiceType.FOURNISSEUR)
        assert len(entries) == 2
        assert any(e.account_number == "401000" for e in entries)
        assert any(e.account_number == "531000" for e in entries)

    @pytest.mark.asyncio
    async def test_source_type_is_payment(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.PAYMENT_RECEIVED_CHEQUE, "511200", "411100")
        inv = await _make_invoice(db_session)
        pay = await _make_payment(db_session, method=PaymentMethod.CHEQUE, invoice_id=inv.id)
        entries = await generate_entries_for_payment(db_session, pay, InvoiceType.CLIENT)
        for e in entries:
            assert e.source_type == EntrySourceType.PAYMENT
            assert e.source_id == pay.id


# ---------------------------------------------------------------------------
# generate_entries_for_deposit
# ---------------------------------------------------------------------------


class TestGenerateEntriesForDeposit:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_rule(self, db_session: AsyncSession) -> None:
        dep = await _make_deposit(db_session)
        result = await generate_entries_for_deposit(db_session, dep)
        assert result == []

    @pytest.mark.asyncio
    async def test_deposit_cheques(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.DEPOSIT_CHEQUES, "512100", "511200")
        dep = await _make_deposit(db_session, dep_type=DepositType.CHEQUES)
        entries = await generate_entries_for_deposit(db_session, dep)
        assert len(entries) == 2
        assert any(e.account_number == "512100" for e in entries)
        assert any(e.account_number == "511200" for e in entries)

    @pytest.mark.asyncio
    async def test_deposit_especes(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.DEPOSIT_ESPECES, "512100", "531000")
        dep = await _make_deposit(db_session, dep_type=DepositType.ESPECES)
        entries = await generate_entries_for_deposit(db_session, dep)
        assert len(entries) == 2
        assert any(e.account_number == "531000" for e in entries)

    @pytest.mark.asyncio
    async def test_source_type_is_deposit(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.DEPOSIT_CHEQUES, "512100", "511200")
        dep = await _make_deposit(db_session)
        entries = await generate_entries_for_deposit(db_session, dep)
        for e in entries:
            assert e.source_type == EntrySourceType.DEPOSIT
            assert e.source_id == dep.id


# ---------------------------------------------------------------------------
# generate_entries_for_salary
# ---------------------------------------------------------------------------


class TestGenerateEntriesForSalary:
    @pytest.mark.asyncio
    async def test_salary_entries_share_one_group_key(self, db_session: AsyncSession) -> None:
        employee = await _make_employee(db_session)
        salary = await _make_salary(db_session, employee.id)
        await _create_fiscal_year(
            db_session,
            name="2024",
            start=date(2024, 1, 1),
            end=date(2024, 12, 31),
        )
        await _seed_one_rule(db_session, TriggerType.SALARY_GROSS, "641000", "421000")
        await _seed_one_rule(
            db_session,
            TriggerType.SALARY_EMPLOYER_CHARGES,
            "645100",
            "431100",
        )
        await _seed_one_rule(db_session, TriggerType.SALARY_PAYMENT, "421000", "512100")

        entries = await generate_entries_for_salary(db_session, salary)

        assert len(entries) == 10
        assert {entry.source_type for entry in entries} == {EntrySourceType.SALARY}
        assert {entry.source_id for entry in entries} == {salary.id}
        assert len({entry.group_key for entry in entries}) == 1
        assert entries[0].group_key is not None
        assert (
            len(
                [entry for entry in entries if entry.account_number == "421000" and entry.debit > 0]
            )
            == 3
        )
        assert any(
            entry.account_number == "431100" and entry.credit == Decimal("220.00")
            for entry in entries
        )
        assert any(
            entry.account_number == "443000" and entry.credit == Decimal("80.00")
            for entry in entries
        )


# ---------------------------------------------------------------------------
# seed_default_rules
# ---------------------------------------------------------------------------


class TestSeedDefaultRules:
    @pytest.mark.asyncio
    async def test_seeds_all_default_rules(self, db_session: AsyncSession) -> None:
        count = await seed_default_rules(db_session)
        assert count == len(DEFAULT_RULES)

    @pytest.mark.asyncio
    async def test_idempotent_on_second_call(self, db_session: AsyncSession) -> None:
        await seed_default_rules(db_session)
        count2 = await seed_default_rules(db_session)
        assert count2 == 0

    @pytest.mark.asyncio
    async def test_backfills_missing_default_rules(self, db_session: AsyncSession) -> None:
        await _seed_one_rule(db_session, TriggerType.SALARY_GROSS, "641000", "421000")

        count = await seed_default_rules(db_session)

        assert count == len(DEFAULT_RULES) - 1

    @pytest.mark.asyncio
    async def test_seeded_rules_have_entries(self, db_session: AsyncSession) -> None:
        await seed_default_rules(db_session)
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from backend.models.accounting_rule import AccountingRule

        result = await db_session.execute(
            select(AccountingRule).options(selectinload(AccountingRule.entries))
        )
        rules = result.scalars().all()
        for rule in rules:
            assert len(rule.entries) >= 2, f"Rule {rule.trigger_type} has no entries"

    @pytest.mark.asyncio
    async def test_inactive_rule_not_matched(self, db_session: AsyncSession) -> None:
        """An inactive rule should not be used by the engine."""
        rule = AccountingRule(
            name="Inactive rule",
            trigger_type=TriggerType.INVOICE_CLIENT_CS,
            is_active=False,
            priority=10,
        )
        db_session.add(rule)
        await db_session.flush()
        db_session.add(
            AccountingRuleEntry(
                rule_id=rule.id,
                account_number="411100",
                side=EntrySide.DEBIT,
                description_template="test",
            )
        )
        db_session.add(
            AccountingRuleEntry(
                rule_id=rule.id,
                account_number="706110",
                side=EntrySide.CREDIT,
                description_template="test",
            )
        )
        await db_session.commit()

        inv = await _make_invoice(db_session, label=InvoiceLabel.CS)
        entries = await generate_entries_for_invoice(db_session, inv)
        assert entries == []
