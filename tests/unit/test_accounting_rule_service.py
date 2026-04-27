"""Unit tests for accounting_rule_service."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_rule import (
    AccountingRule,
    AccountingRuleEntry,
    EntrySide,
    TriggerType,
)
from backend.schemas.accounting_rule import AccountingRuleEntryCreate, AccountingRuleUpdate
from backend.services.accounting_rule_service import (
    _render_template,
    get_rule,
    list_rules,
    preview_rule,
    update_rule,
)


async def _make_rule(
    db: AsyncSession,
    *,
    name: str = "Test Rule",
    trigger: TriggerType = TriggerType.MANUAL,
    entries: list[tuple[str, EntrySide, str]] | None = None,
) -> AccountingRule:
    rule = AccountingRule(
        name=name,
        trigger_type=trigger,
        is_active=True,
        priority=10,
    )
    db.add(rule)
    await db.flush()

    if entries:
        for acct, side, tpl in entries:
            db.add(
                AccountingRuleEntry(
                    rule_id=rule.id,
                    account_number=acct,
                    side=side,
                    description_template=tpl,
                )
            )
    await db.commit()
    await db.refresh(rule)
    return rule


class TestListRules:
    @pytest.mark.asyncio
    async def test_empty(self, db_session: AsyncSession) -> None:
        result = await list_rules(db_session)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_rules(self, db_session: AsyncSession) -> None:
        await _make_rule(db_session, name="R1", trigger=TriggerType.MANUAL)
        await _make_rule(db_session, name="R2", trigger=TriggerType.BANK_FEES)
        result = await list_rules(db_session)
        assert len(result) == 2


class TestGetRule:
    @pytest.mark.asyncio
    async def test_returns_existing(self, db_session: AsyncSession) -> None:
        rule = await _make_rule(db_session)
        found = await get_rule(db_session, rule.id)
        assert found is not None
        assert found.name == "Test Rule"

    @pytest.mark.asyncio
    async def test_returns_none(self, db_session: AsyncSession) -> None:
        assert await get_rule(db_session, 999) is None


class TestUpdateRule:
    @pytest.mark.asyncio
    async def test_update_scalar_fields(self, db_session: AsyncSession) -> None:
        rule = await _make_rule(db_session)
        updated = await update_rule(
            db_session,
            rule,
            AccountingRuleUpdate(name="New Name", priority=5, description="Desc"),
        )
        assert updated.name == "New Name"
        assert updated.priority == 5
        assert updated.description == "Desc"

    @pytest.mark.asyncio
    async def test_replace_entries(self, db_session: AsyncSession) -> None:
        rule = await _make_rule(
            db_session,
            entries=[("512000", EntrySide.DEBIT, "{{label}}")],
        )
        # Reload with eager-loaded entries (required by update_rule)
        reloaded_rule = await get_rule(db_session, rule.id)
        assert reloaded_rule is not None
        assert len(reloaded_rule.entries) == 1

        updated = await update_rule(
            db_session,
            reloaded_rule,
            AccountingRuleUpdate(
                entries=[
                    AccountingRuleEntryCreate(
                        account_number="411000", side=EntrySide.DEBIT, description_template="D"
                    ),
                    AccountingRuleEntryCreate(
                        account_number="706000", side=EntrySide.CREDIT, description_template="C"
                    ),
                ]
            ),
        )
        reloaded = await get_rule(db_session, updated.id)
        assert reloaded is not None
        assert len(reloaded.entries) == 2


class TestRenderTemplate:
    def test_basic_substitution(self) -> None:
        assert _render_template("Paiement {{label}}", {"label": "facture 1"}) == (
            "Paiement facture 1"
        )

    def test_unknown_key_left_as_is(self) -> None:
        assert _render_template("{{unknown}}", {}) == "{{unknown}}"

    def test_multiple_keys(self) -> None:
        result = _render_template("{{label}} — {{amount}}", {"label": "Test", "amount": "100"})
        assert result == "Test — 100"


class TestPreviewRule:
    @pytest.mark.asyncio
    async def test_returns_none_if_rule_not_found(self, db_session: AsyncSession) -> None:
        result = await preview_rule(db_session, 999, Decimal("100"), "Test")
        assert result is None

    @pytest.mark.asyncio
    async def test_generates_preview_entries(self, db_session: AsyncSession) -> None:
        rule = await _make_rule(
            db_session,
            entries=[
                ("512000", EntrySide.DEBIT, "Débit {{label}}"),
                ("411000", EntrySide.CREDIT, "Crédit {{label}}"),
            ],
        )

        result = await preview_rule(db_session, rule.id, Decimal("250.00"), "Test facture")
        assert result is not None
        assert len(result) == 2
        assert result[0].debit == Decimal("250.00")
        assert result[0].credit == Decimal("0")
        assert result[0].label == "Débit Test facture"
        assert result[1].debit == Decimal("0")
        assert result[1].credit == Decimal("250.00")
