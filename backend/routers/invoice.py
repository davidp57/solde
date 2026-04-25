"""Invoices API router — CRUD, status changes, PDF generation, file upload, email."""

import logging
import uuid
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.invoice import InvoiceStatus, InvoiceType
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.invoice import (
    InvoiceCreate,
    InvoiceRead,
    InvoiceStatusUpdate,
    InvoiceUpdate,
)
from backend.services import invoice as invoice_service
from backend.services import settings as settings_service
from backend.services.invoice import InvoiceDeleteError, InvoiceStatusError, InvoiceUpdateError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["invoices"])

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]

# Allowed MIME types for supplier invoice file uploads
_ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# Magic bytes for allowed file types
_MAGIC_BYTES: list[bytes] = [
    b"\x25\x50\x44\x46",  # PDF: %PDF
    b"\xff\xd8\xff",  # JPEG
    b"\x89\x50\x4e\x47",  # PNG: \x89PNG
]


def _content_matches_allowed_type(content: bytes) -> bool:
    """Return True if the file's magic bytes match an allowed type."""
    if any(content[: len(magic)] == magic for magic in _MAGIC_BYTES):
        return True
    # WebP: "RIFF" at offset 0 and "WEBP" at offset 8
    return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"


@router.get("/", response_model=list[InvoiceRead])
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    invoice_type: InvoiceType | None = Query(default=None),
    invoice_status: InvoiceStatus | None = Query(default=None),
    contact_id: int | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    year: int | None = Query(default=None, ge=2000, le=2100),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[InvoiceRead]:
    """List invoices with optional filters."""
    return await invoice_service.list_invoices(
        db,
        invoice_type=invoice_type,
        status=invoice_status,
        contact_id=contact_id,
        from_date=from_date,
        to_date=to_date,
        year=year,
        skip=skip,
        limit=limit,
    )  # type: ignore[return-value]


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> InvoiceRead:
    """Create a new invoice."""
    return await invoice_service.create_invoice(db, payload)  # type: ignore[return-value]


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> InvoiceRead:
    """Get a single invoice by ID."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice  # type: ignore[return-value]


@router.put("/{invoice_id}", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> InvoiceRead:
    """Partially update an invoice."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        return await invoice_service.update_invoice(db, invoice, payload)  # type: ignore[return-value]
    except InvoiceUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{invoice_id}/status", response_model=InvoiceRead)
async def update_status(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> InvoiceRead:
    """Change the status of an invoice (enforces valid transitions)."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        return await invoice_service.update_invoice_status(  # type: ignore[return-value]
            db, invoice, payload.status
        )
    except InvoiceStatusError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/{invoice_id}/duplicate",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_invoice(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> InvoiceRead:
    """Create a draft copy of an existing invoice."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return await invoice_service.duplicate_invoice(db, invoice)  # type: ignore[return-value]


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> None:
    """Delete an invoice. Only draft invoices can be deleted."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        await invoice_service.delete_invoice(db, invoice)
    except InvoiceDeleteError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    """Generate and return the PDF for a client invoice."""
    from backend.services import pdf_service  # noqa: PLC0415 — lazy import

    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.type != InvoiceType.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF generation is only available for client invoices",
        )

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415

    result = await db.execute(select(Contact).where(Contact.id == invoice.contact_id))
    contact = result.scalar_one_or_none()
    contact_name = contact.nom if contact else "Inconnu"
    if contact and contact.prenom:
        contact_name = f"{contact.prenom} {contact.nom}"

    app_settings = await settings_service.get_settings(db)
    try:
        pdf_bytes = pdf_service.generate_invoice_pdf(invoice, contact_name, app_settings)
    except Exception as exc:
        logger.exception("PDF generation failed for invoice %d", invoice_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation failed",
        ) from exc

    pdf_path = pdf_service.save_invoice_pdf(invoice.number, pdf_bytes)
    await invoice_service.set_pdf_path(db, invoice, pdf_path)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"facture_{invoice.number}.pdf",
    )


@router.post("/{invoice_id}/send-email", status_code=status.HTTP_204_NO_CONTENT)
async def send_invoice_email(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> None:
    """Generate PDF and send the invoice by email to the contact."""
    from backend.services import email_service, pdf_service  # noqa: PLC0415

    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.type != InvoiceType.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sending is only available for client invoices",
        )

    app_settings = await settings_service.get_settings(db)

    # Check SMTP is configured
    if not all(
        [
            app_settings.smtp_host,
            app_settings.smtp_user,
            app_settings.smtp_password,
            app_settings.smtp_from_email,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMTP is not configured",
        )

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415

    result = await db.execute(select(Contact).where(Contact.id == invoice.contact_id))
    contact = result.scalar_one_or_none()
    if contact is None or not contact.email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Contact has no email address",
        )

    contact_name = contact.nom
    if contact.prenom:
        contact_name = f"{contact.prenom} {contact.nom}"

    pdf_bytes = pdf_service.generate_invoice_pdf(invoice, contact_name, app_settings)

    try:
        email_service.send_invoice_email(
            smtp_host=app_settings.smtp_host,  # type: ignore[arg-type]
            smtp_port=app_settings.smtp_port,
            smtp_user=app_settings.smtp_user,  # type: ignore[arg-type]
            smtp_password=app_settings.smtp_password,  # type: ignore[arg-type]
            smtp_from_email=app_settings.smtp_from_email,  # type: ignore[arg-type]
            smtp_use_tls=app_settings.smtp_use_tls,
            recipient_email=contact.email,
            invoice_number=invoice.number,
            association_name=app_settings.association_name,
            pdf_bytes=pdf_bytes,
        )
    except email_service.EmailSendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Email delivery failed: {exc}",
        ) from exc

    # Auto-transition draft → sent
    from backend.models.invoice import InvoiceStatus  # noqa: PLC0415

    if invoice.status == InvoiceStatus.DRAFT:
        await invoice_service.update_invoice_status(db, invoice, InvoiceStatus.SENT)


@router.post("/{invoice_id}/file", response_model=InvoiceRead)
async def upload_invoice_file(
    invoice_id: int,
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> InvoiceRead:
    """Upload a file attachment for a supplier invoice."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.type != InvoiceType.FOURNISSEUR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File upload is only for supplier invoices",
        )

    # Validate content type
    if file.content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' is not allowed. Use PDF, JPEG, PNG, or WebP.",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 10 MB limit",
        )

    # Validate actual file content against magic bytes (not just the client-supplied MIME type)
    if not _content_matches_allowed_type(content):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File content does not match an allowed type (PDF, JPEG, PNG, WebP).",
        )

    # Save with a UUID-based name to prevent path traversal
    suffix = Path(file.filename or "upload").suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    upload_dir = Path("data/uploads/invoices").resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_name
    file_path.write_bytes(content)

    return await invoice_service.set_file_path(  # type: ignore[return-value]
        db, invoice, str(file_path)
    )
