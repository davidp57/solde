"""Accounting rules service — CRUD with eager-loaded entries."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.accounting_rule import AccountingRule, AccountingRuleEntry
from backend.schemas.accounting_rule import AccountingRuleUpdate


async def list_rules(db: AsyncSession) -> list[AccountingRule]:
    result = await db.execute(
        select(AccountingRule)
        .options(selectinload(AccountingRule.entries))
        .order_by(AccountingRule.priority.asc(), AccountingRule.id.asc())
    )
    return list(result.scalars().all())


async def get_rule(db: AsyncSession, rule_id: int) -> AccountingRule | None:
    result = await db.execute(
        select(AccountingRule)
        .where(AccountingRule.id == rule_id)
        .options(selectinload(AccountingRule.entries))
    )
    return result.scalar_one_or_none()


async def update_rule(
    db: AsyncSession, rule: AccountingRule, payload: AccountingRuleUpdate
) -> AccountingRule:
    for field in ("name", "is_active", "priority", "description"):
        value = getattr(payload, field)
        if value is not None:
            setattr(rule, field, value)

    if payload.entries is not None:
        # Replace all rule entries
        for existing in list(rule.entries):
            await db.delete(existing)
        await db.flush()
        for entry_data in payload.entries:
            db.add(
                AccountingRuleEntry(
                    rule_id=rule.id,
                    account_number=entry_data.account_number,
                    side=entry_data.side,
                    description_template=entry_data.description_template,
                )
            )

    await db.commit()
    await db.refresh(rule)
    return rule
