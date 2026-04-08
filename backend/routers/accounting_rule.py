"""Accounting rules API — list, update, seed defaults."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.accounting_rule import AccountingRuleRead, AccountingRuleUpdate
from backend.services import accounting_rule_service
from backend.services.accounting_engine import seed_default_rules

router = APIRouter(prefix="/accounting/rules", tags=["accounting"])

_AdminAccess = Annotated[
    User,
    Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[User, Depends(get_current_user)]


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
