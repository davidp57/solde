"""Excel import API — upload and import Gestion / Comptabilité Excel files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.services import excel_import

router = APIRouter(prefix="/import", tags=["import"])

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB hard limit

_WriteAccess = Annotated[User, Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN))]


@dataclass(frozen=True)
class _TestImportShortcut:
    alias: str
    label: str
    import_type: str
    file_path: str | None
    order: int


async def _read_limited(upload: UploadFile) -> bytes:
    """Read upload content, enforcing the size limit."""
    content = await upload.read(_MAX_UPLOAD_BYTES + 1)
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (limite : 10 Mo)",
        )
    return content


def _check_excel_extension(filename: str | None) -> None:
    if not filename or not filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)",
        )


def _read_path_limited(file_path: Path) -> bytes:
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Fichier de test introuvable : {file_path}",
        )

    size = file_path.stat().st_size
    if size > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (limite : 10 Mo)",
        )

    return file_path.read_bytes()


def _get_test_import_shortcuts() -> list[_TestImportShortcut]:
    settings = get_settings()
    return [
        _TestImportShortcut(
            alias="gestion-2024",
            label="Gestion 2024",
            import_type="gestion",
            file_path=settings.test_import_gestion_2024_path,
            order=1,
        ),
        _TestImportShortcut(
            alias="gestion-2025",
            label="Gestion 2025",
            import_type="gestion",
            file_path=settings.test_import_gestion_2025_path,
            order=2,
        ),
        _TestImportShortcut(
            alias="comptabilite-2024",
            label="Comptabilité 2024",
            import_type="comptabilite",
            file_path=settings.test_import_comptabilite_2024_path,
            order=3,
        ),
        _TestImportShortcut(
            alias="comptabilite-2025",
            label="Comptabilité 2025",
            import_type="comptabilite",
            file_path=settings.test_import_comptabilite_2025_path,
            order=4,
        ),
    ]


def _require_test_import_shortcuts_enabled() -> None:
    if not get_settings().enable_test_import_shortcuts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def _serialize_test_import_shortcut(shortcut: _TestImportShortcut) -> dict[str, object]:
    path = Path(shortcut.file_path) if shortcut.file_path else None
    available = bool(path and path.is_file())
    message = None
    if shortcut.file_path is None:
        message = "Chemin non configuré"
    elif not available:
        message = "Fichier introuvable"

    return {
        "alias": shortcut.alias,
        "label": shortcut.label,
        "import_type": shortcut.import_type,
        "order": shortcut.order,
        "available": available,
        "file_name": path.name if path else None,
        "message": message,
    }


def _get_test_import_shortcut_by_alias(alias: str) -> _TestImportShortcut:
    for shortcut in _get_test_import_shortcuts():
        if shortcut.alias == alias:
            return shortcut
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raccourci d'import inconnu")


async def _run_test_import_shortcut(
    shortcut: _TestImportShortcut,
    db: AsyncSession,
) -> dict[str, object]:
    if shortcut.file_path is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Chemin non configuré pour {shortcut.label}",
        )

    path = Path(shortcut.file_path)
    _check_excel_extension(path.name)
    content = _read_path_limited(path)
    if shortcut.import_type == "gestion":
        result = await excel_import.import_gestion_file(db, content, path.name)
    else:
        result = await excel_import.import_comptabilite_file(db, content, path.name)
    return result.to_dict()


@router.post("/excel/gestion", status_code=status.HTTP_200_OK)
async def import_gestion(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> dict[str, object]:
    """Import contacts, invoices and payments from a 'Gestion YYYY.xlsx' file."""
    _check_excel_extension(file.filename)
    content = await _read_limited(file)
    result = await excel_import.import_gestion_file(db, content, file.filename)
    return result.to_dict()


@router.post("/excel/comptabilite", status_code=status.HTTP_200_OK)
async def import_comptabilite(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> dict[str, object]:
    """Import accounting entries from a 'Comptabilité YYYY.xlsx' file."""
    _check_excel_extension(file.filename)
    content = await _read_limited(file)
    result = await excel_import.import_comptabilite_file(db, content, file.filename)
    return result.to_dict()


@router.post("/excel/gestion/preview", status_code=status.HTTP_200_OK)
async def preview_gestion(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> dict[str, object]:
    """Dry-run parse of a Gestion file — returns estimated row counts without importing."""
    _check_excel_extension(file.filename)
    content = await _read_limited(file)
    result = await excel_import.preview_gestion_file(db, content)
    return result.to_dict()


@router.post("/excel/comptabilite/preview", status_code=status.HTTP_200_OK)
async def preview_comptabilite(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> dict[str, object]:
    """Dry-run parse of a Comptabilité file — returns estimated row counts without importing."""
    _check_excel_extension(file.filename)
    content = await _read_limited(file)
    result = await excel_import.preview_comptabilite_file(db, content)
    return result.to_dict()


@router.get("/excel/test-shortcuts", status_code=status.HTTP_200_OK)
async def list_test_import_shortcuts(
    _: _WriteAccess,
) -> list[dict[str, object]]:
    """List temporary dev-only import shortcuts exposed in the import page."""
    _require_test_import_shortcuts_enabled()
    return [_serialize_test_import_shortcut(shortcut) for shortcut in _get_test_import_shortcuts()]


@router.post("/excel/test-shortcuts/{alias}", status_code=status.HTTP_200_OK)
async def run_test_import_shortcut(
    alias: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> dict[str, object]:
    """Run a temporary dev-only import shortcut without preview confirmation."""
    _require_test_import_shortcuts_enabled()
    shortcut = _get_test_import_shortcut_by_alias(alias)
    return await _run_test_import_shortcut(shortcut, db)
