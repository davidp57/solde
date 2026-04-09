"""Dashboard API — KPIs and monthly chart data."""

from datetime import datetime
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
) -> dict:
    return await dashboard_service.get_dashboard(db)


@router.get("/chart/monthly")
async def get_monthly_chart(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    year: int = Query(default=datetime.now().year),
) -> list[dict]:
    return await dashboard_service.get_monthly_chart(db, year)
