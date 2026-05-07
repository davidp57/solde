"""Bank API router — aggregates transactions, import, and deposit sub-routers."""

from fastapi import APIRouter

from backend.routers.bank_deposits import router as deposits_router
from backend.routers.bank_import import router as import_router
from backend.routers.bank_transactions import router as transactions_router

router = APIRouter(prefix="/bank", tags=["bank"])
router.include_router(transactions_router)
router.include_router(import_router)
router.include_router(deposits_router)
