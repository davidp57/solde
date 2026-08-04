"""Documents API router — upload, list, download and remove free-form documents."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import api_error, not_found
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.document import DocumentRead, DocumentTagRead, DocumentUpdate
from backend.services import document_service
from backend.services.audit_service import AuditAction, record_audit
from backend.services.document_service import MAX_DOCUMENT_BYTES, DocumentError

router = APIRouter(prefix="/documents", tags=["documents"])

# Filing is the secretary's job first; making it an administrator's would defeat it.
_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]
# Read-only accounts already see everything else in the application.
_ReadAccess = Annotated[
    User,
    Depends(
        require_role(UserRole.READONLY, UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)
    ),
]


def _raise_for(error: DocumentError) -> None:
    """Map a service refusal onto its HTTP status."""
    if error.code == "FILE_TOO_LARGE":
        raise api_error(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, error.code, str(error))
    if error.code in {"FISCAL_YEAR_NOT_FOUND", "DOCUMENT_FILE_MISSING"}:
        raise api_error(status.HTTP_404_NOT_FOUND, error.code, str(error))
    raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, error.code, str(error))


def _content_disposition(filename: str) -> str:
    """Build the header, dropping what would let a filename break out of it."""
    safe = filename.replace('"', "").replace("\r", "").replace("\n", "").strip()
    return f'attachment; filename="{safe or "document"}"'


@router.post("/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: _WriteAccess,
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    fiscal_year_id: Annotated[int | None, Form()] = None,
    tags: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
) -> DocumentRead:
    """Store an uploaded document with its metadata."""
    # Read one byte past the ceiling so an oversized file is caught without being
    # fully buffered.
    content = await file.read(MAX_DOCUMENT_BYTES + 1)
    try:
        document = await document_service.store_document(
            db,
            title=title,
            filename=file.filename or "document",
            content=content,
            fiscal_year_id=fiscal_year_id,
            tags=document_service.parse_tags(tags),
            notes=notes,
            uploaded_by=user.username,
        )
    except DocumentError as exc:
        _raise_for(exc)
        raise  # pragma: no cover — _raise_for always raises

    await record_audit(
        db,
        action=AuditAction.DOCUMENT_UPLOADED,
        actor=user,
        target_id=document.id,
        target_type="document",
        detail={"title": document.title, "filename": document.filename},
    )
    return document


@router.get("/", response_model=list[DocumentRead])
async def list_documents(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    fiscal_year_id: int | None = Query(default=None),
    without_fiscal_year: bool = Query(default=False),
    tag: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[DocumentRead]:
    """List documents, most recently uploaded first."""
    documents, total = await document_service.list_documents(
        db,
        fiscal_year_id=fiscal_year_id,
        without_fiscal_year=without_fiscal_year,
        tag=tag,
        search=search,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    return documents


@router.get("/tags", response_model=list[DocumentTagRead])
async def list_document_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> list[DocumentTagRead]:
    """List the tags in use, so the same idea is not filed under two spellings."""
    return await document_service.list_tags(db)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> DocumentRead:
    document = await document_service.get_document(db, document_id)
    if document is None:
        raise not_found("Document")
    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> FileResponse:
    """Serve the stored file under its original name."""
    try:
        found = await document_service.get_document_file(db, document_id)
    except DocumentError as exc:
        _raise_for(exc)
        raise  # pragma: no cover — _raise_for always raises
    if found is None:
        raise not_found("Document")

    path, filename, mime_type = found
    return FileResponse(
        str(path),
        media_type=mime_type,
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: int,
    payload: DocumentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: _WriteAccess,
) -> DocumentRead:
    """Update a document's metadata. The stored file is never replaced."""
    try:
        document = await document_service.update_document(db, document_id, payload)
    except DocumentError as exc:
        _raise_for(exc)
        raise  # pragma: no cover — _raise_for always raises
    if document is None:
        raise not_found("Document")

    await record_audit(
        db,
        action=AuditAction.DOCUMENT_UPDATED,
        actor=user,
        target_id=document.id,
        target_type="document",
        detail={"title": document.title},
    )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: _WriteAccess,
) -> None:
    """Delete a document and its file."""
    document = await document_service.get_document(db, document_id)
    if document is None:
        raise not_found("Document")

    # Audited before the row goes: SQLAlchemy cascades the pending delete over the
    # session, and a log added afterwards does not survive the flush.
    await record_audit(
        db,
        action=AuditAction.DOCUMENT_DELETED,
        actor=user,
        target_id=document_id,
        target_type="document",
        detail={"title": document.title, "filename": document.filename},
    )
    await document_service.delete_document(db, document_id)
