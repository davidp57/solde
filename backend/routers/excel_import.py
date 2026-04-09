"""Excel import API — upload and import Gestion / Comptabilité Excel files."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.services import excel_import

router = APIRouter(prefix="/import", tags=["import"])

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB hard limit

_WriteAccess = Annotated[User, Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN))]


async def _read_limited(upload: UploadFile) -> bytes:
    """Read upload content, enforcing the size limit."""
    content = await upload.read(_MAX_UPLOAD_BYTES + 1)
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (limite : 10 Mo)",
        )
    return content


@router.post("/excel/gestion", status_code=status.HTTP_200_OK)
async def import_gestion(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> dict:
    """Import contacts, invoices and payments from a 'Gestion YYYY.xlsx' file."""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)",
        )
    content = await _read_limited(file)
    result = await excel_import.import_gestion_file(db, content)
    return result.to_dict()


@router.post("/excel/comptabilite", status_code=status.HTTP_200_OK)
async def import_comptabilite(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> dict:
    """Import accounting entries from a 'Comptabilité YYYY.xlsx' file."""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)",
        )
    content = await _read_limited(file)
    result = await excel_import.import_comptabilite_file(db, content)
    return result.to_dict()
