"""Dashboard API — KPIs and monthly chart data."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_ReadAccess = Annotated[User, Depends(get_current_user)]


@router.get("/")
async def get_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> dict[str, object]:
    return await dashboard_service.get_dashboard(db)


@router.get("/chart/monthly")
async def get_monthly_chart(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    fiscal_year_id: int | None = Query(default=None),
) -> list[dict[str, Decimal | str]]:
    return await dashboard_service.get_monthly_chart(db, fiscal_year_id)


@router.get("/chart/resources")
async def get_resources_chart(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    months: int = Query(default=12, ge=1, le=36),
) -> list[dict[str, Decimal | str]]:
    return await dashboard_service.get_resources_chart(db, months=months)
