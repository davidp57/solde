"""Accounting rules API — list, update, seed defaults."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.accounting_rule import (
    AccountingRuleCreate,
    AccountingRuleRead,
    AccountingRuleUpdate,
    RulePreviewEntry,
    RulePreviewRequest,
)
from backend.services import accounting_rule_service
from backend.services.accounting_engine import seed_default_rules

router = APIRouter(prefix="/accounting/rules", tags=["accounting"])

_AdminAccess = Annotated[
    User,
    Depends(require_role(UserRole.ADMIN)),
]
_ReadAccess = Annotated[
    User,
    Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN)),
]


@router.get("/", response_model=list[AccountingRuleRead])
async def list_rules(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> list[AccountingRuleRead]:
    rules = await accounting_rule_service.list_rules(db)
    return rules  # type: ignore[return-value]


@router.get("/{rule_id}", response_model=AccountingRuleRead)
async def get_rule(
    rule_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> AccountingRuleRead:
    rule = await accounting_rule_service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule  # type: ignore[return-value]


@router.post("/", response_model=AccountingRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: AccountingRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminAccess,
) -> AccountingRuleRead:
    existing = await accounting_rule_service.list_rules(db)
    if any(r.trigger_type == payload.trigger_type for r in existing):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A rule with this trigger_type already exists",
        )
    rule = await accounting_rule_service.create_rule(db, payload)
    return rule  # type: ignore[return-value]


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminAccess,
) -> None:
    rule = await accounting_rule_service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await accounting_rule_service.delete_rule(db, rule)


@router.put("/{rule_id}", response_model=AccountingRuleRead)
async def update_rule(
    rule_id: int,
    payload: AccountingRuleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminAccess,
) -> AccountingRuleRead:
    rule = await accounting_rule_service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    updated = await accounting_rule_service.update_rule(db, rule, payload)
    return updated  # type: ignore[return-value]


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_rules(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminAccess,
) -> dict[str, int]:
    """Insert default accounting rules if none exist. Returns the number of rules inserted."""
    count = await seed_default_rules(db)
    return {"inserted": count}


@router.post("/{rule_id}/preview", response_model=list[RulePreviewEntry])
async def preview_rule(
    rule_id: int,
    payload: RulePreviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> list[RulePreviewEntry]:
    """Simulate the accounting entries that a rule would generate, without writing to the DB."""
    entries = await accounting_rule_service.preview_rule(
        db,
        rule_id,
        amount=payload.amount,
        label=payload.label,
        entry_date=payload.entry_date,
    )
    if entries is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return entries
