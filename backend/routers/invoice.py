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
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import api_error, conflict, not_found, unprocessable
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.invoice import (
    BulkArchiveRequest,
    BulkArchiveResult,
    InvoiceCreate,
    InvoiceEmailPreview,
    InvoiceEmailSendRequest,
    InvoiceRead,
    InvoiceStatusUpdate,
    InvoiceUpdate,
)
from backend.services import invoice as invoice_service
from backend.services import settings as settings_service
from backend.services.audit_service import AuditAction, record_audit
from backend.services.invoice import (
    BlockedContactError,
    InvoiceDeleteError,
    InvoiceStatusError,
    InvoiceUpdateError,
    archive_invoice,
)

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


@router.get("/next_number")
async def preview_next_number(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> dict[str, str]:
    """Preview the next client invoice number (no side effects)."""
    number = await invoice_service.peek_next_client_number(db)
    return {"number": number}


@router.get("/", response_model=list[InvoiceRead])
async def list_invoices(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    invoice_type: InvoiceType | None = Query(default=None),
    invoice_status: InvoiceStatus | None = Query(default=None),
    contact_id: int | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    year: int | None = Query(default=None, ge=2000, le=2100),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=1000, ge=1, le=5000),
) -> list[Invoice]:
    """List invoices with optional filters."""
    items = await invoice_service.list_invoices(
        db,
        invoice_type=invoice_type,
        status=invoice_status,
        contact_id=contact_id,
        from_date=from_date,
        to_date=to_date,
        year=year,
        skip=skip,
        limit=limit,
    )
    total = await invoice_service.count_invoices(
        db,
        invoice_type=invoice_type,
        status=invoice_status,
        contact_id=contact_id,
        from_date=from_date,
        to_date=to_date,
        year=year,
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> Invoice:
    """Create a new invoice."""
    try:
        invoice = await invoice_service.create_invoice(db, payload)
    except BlockedContactError as exc:
        raise unprocessable(
            "CONTACT_BLOCKED", "Contact is marked as blocked: invoice creation denied"
        ) from exc
    await record_audit(
        db,
        action=AuditAction.INVOICE_CREATED,
        actor=current_user,
        target_id=invoice.id,
        target_type="invoice",
        detail={
            "number": invoice.number,
            "type": invoice.type,
            "total_amount": str(invoice.total_amount),
        },
    )
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> Invoice:
    """Get a single invoice by ID."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> Invoice:
    """Partially update an invoice."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    try:
        updated = await invoice_service.update_invoice(db, invoice, payload)
    except InvoiceUpdateError as exc:
        raise conflict("INVOICE_OPERATION_FAILED", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.INVOICE_UPDATED,
        actor=current_user,
        target_id=invoice_id,
        target_type="invoice",
        detail={"number": invoice.number},
    )
    return updated


@router.patch("/{invoice_id}/status", response_model=InvoiceRead)
async def update_status(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> Invoice:
    """Change the status of an invoice (enforces valid transitions)."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    old_status = invoice.status
    try:
        updated = await invoice_service.update_invoice_status(db, invoice, payload.status)
    except InvoiceStatusError as exc:
        raise conflict("INVOICE_OPERATION_FAILED", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.INVOICE_STATUS_CHANGED,
        actor=current_user,
        target_id=invoice_id,
        target_type="invoice",
        detail={"number": invoice.number, "from": old_status, "to": payload.status},
    )
    return updated


@router.post("/{invoice_id}/write-off", response_model=InvoiceRead)
async def write_off_invoice(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> Invoice:
    """Mark a client invoice as irrecoverable and generate write-off accounting entries."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    try:
        updated = await invoice_service.write_off_invoice(db, invoice)
    except InvoiceStatusError as exc:
        raise conflict("INVOICE_OPERATION_FAILED", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.INVOICE_WRITTEN_OFF,
        actor=current_user,
        target_id=invoice_id,
        target_type="invoice",
        detail={"number": invoice.number},
    )
    return updated


@router.post("/{invoice_id}/restore-from-writeoff", response_model=InvoiceRead)
async def restore_from_writeoff(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> Invoice:
    """Restore an irrecoverable invoice: generate reversal entries and recompute status."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    try:
        updated = await invoice_service.restore_from_writeoff(db, invoice)
    except InvoiceStatusError as exc:
        raise conflict("INVOICE_OPERATION_FAILED", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.INVOICE_RESTORED_FROM_WRITEOFF,
        actor=current_user,
        target_id=invoice_id,
        target_type="invoice",
        detail={"number": invoice.number},
    )
    return updated


@router.post("/bulk-archive", response_model=BulkArchiveResult)
async def bulk_archive_invoices(
    payload: BulkArchiveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BulkArchiveResult:
    """Archive a batch of PAID client invoices.

    Non-PAID invoices are silently skipped (counted in 'skipped').
    Returns a summary of archived, skipped, and error counts.
    """
    archived_count = 0
    skipped_count = 0
    error_msgs: list[str] = []
    archived_numbers: list[str] = []

    for invoice_id in payload.invoice_ids:
        invoice = await invoice_service.get_invoice(db, invoice_id)
        if invoice is None:
            skipped_count += 1
            continue
        if invoice.status != InvoiceStatus.PAID:
            skipped_count += 1
            continue
        try:
            updated = await archive_invoice(db, invoice)
            archived_count += 1
            archived_numbers.append(updated.number)
        except InvoiceStatusError as exc:
            error_msgs.append(f"{invoice.number}: {exc}")
        except Exception as exc:
            logger.exception("Unexpected error archiving invoice %d", invoice_id)
            error_msgs.append(f"invoice#{invoice_id}: {exc}")

    if archived_numbers:
        await record_audit(
            db,
            action=AuditAction.INVOICE_BULK_ARCHIVED,
            actor=current_user,
            target_id=None,
            target_type="invoice",
            detail={"count": archived_count, "numbers": archived_numbers},
        )

    return BulkArchiveResult(
        archived=archived_count,
        skipped=skipped_count,
        errors=error_msgs,
    )


@router.post(
    "/{invoice_id}/duplicate",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_invoice(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> Invoice:
    """Create a draft copy of an existing invoice."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    duplicate = await invoice_service.duplicate_invoice(db, invoice)
    await record_audit(
        db,
        action=AuditAction.INVOICE_DUPLICATED,
        actor=current_user,
        target_id=duplicate.id,
        target_type="invoice",
        detail={"source_id": invoice_id, "source_number": invoice.number},
    )
    return duplicate


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> None:
    """Delete an invoice. Only draft invoices can be deleted."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    detail = {"number": invoice.number, "type": invoice.type}
    try:
        await invoice_service.delete_invoice(db, invoice)
    except InvoiceDeleteError as exc:
        raise conflict("INVOICE_OPERATION_FAILED", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.INVOICE_DELETED,
        actor=current_user,
        target_id=invoice_id,
        target_type="invoice",
        detail=detail,
    )


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
        raise not_found("Invoice")
    if invoice.type != InvoiceType.CLIENT:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "INVOICE_PDF_CLIENT_ONLY",
            "PDF generation is only available for client invoices",
        )

    # Archived invoices can carry an imported source PDF; return it directly when present.
    if invoice.status == InvoiceStatus.ARCHIVED and invoice.pdf_path:
        # Resolve path: if relative, relative to project root; if absolute, use as-is
        stored_pdf = Path(invoice.pdf_path)
        pdf_path = stored_pdf if stored_pdf.is_absolute() else Path.cwd() / stored_pdf

        if pdf_path.is_file():
            return FileResponse(
                path=str(pdf_path),
                media_type="application/pdf",
                filename=f"facture_{invoice.number}.pdf",
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
        pdf_bytes = pdf_service.generate_invoice_pdf(
            invoice, contact_name, app_settings, contact.adresse if contact else None
        )
    except Exception as exc:
        logger.exception("PDF generation failed for invoice %d", invoice_id)
        raise api_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INVOICE_PDF_GENERATION_FAILED",
            "PDF generation failed",
        ) from exc

    generated_pdf_path = pdf_service.save_invoice_pdf(invoice.number, pdf_bytes)
    await invoice_service.set_pdf_path(db, invoice, generated_pdf_path)

    return FileResponse(
        path=generated_pdf_path,
        media_type="application/pdf",
        filename=f"facture_{invoice.number}.pdf",
    )


@router.get("/{invoice_id}/email-preview", response_model=InvoiceEmailPreview)
async def get_invoice_email_preview(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> InvoiceEmailPreview:
    """Return the pre-composed email subject, body and recipient for an invoice."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.services import email_service  # noqa: PLC0415

    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    if invoice.type != InvoiceType.CLIENT:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "INVOICE_EMAIL_CLIENT_ONLY",
            "Email preview is only available for client invoices",
        )

    app_settings = await settings_service.get_settings(db)

    result = await db.execute(select(Contact).where(Contact.id == invoice.contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise not_found("Contact")

    recipients: list[str] = []
    if contact.email:
        recipients.append(contact.email)
    for ce in contact.emails:
        if ce.email and ce.email not in recipients:
            recipients.append(ce.email)

    if not recipients:
        raise unprocessable("CONTACT_NO_EMAIL", "Contact has no email address")

    return InvoiceEmailPreview(
        recipients=recipients,
        subject=email_service.compose_subject(
            invoice.number,
            invoice.description,
            app_settings.association_name,
            template=app_settings.email_subject_template,
        ),
        body=email_service.compose_body(
            invoice.number,
            invoice.description,
            app_settings.association_name,
            template=app_settings.email_body_template,
        ),
    )


@router.post("/{invoice_id}/send-email", status_code=status.HTTP_204_NO_CONTENT)
async def send_invoice_email(
    invoice_id: int,
    payload: InvoiceEmailSendRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> None:
    """Generate PDF and send the invoice by email to the contact."""
    from backend.services import email_service, pdf_service  # noqa: PLC0415

    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    if invoice.type != InvoiceType.CLIENT:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "INVOICE_EMAIL_CLIENT_ONLY",
            "Email sending is only available for client invoices",
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
        raise api_error(
            status.HTTP_503_SERVICE_UNAVAILABLE, "SMTP_NOT_CONFIGURED", "SMTP is not configured"
        )

    from sqlalchemy import select  # noqa: PLC0415
    from sqlalchemy.orm import selectinload  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415

    result = await db.execute(
        select(Contact)
        .where(Contact.id == invoice.contact_id)
        .options(selectinload(Contact.emails))
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        raise not_found("Contact")
    if not payload.recipients:
        raise unprocessable("EMAIL_NO_RECIPIENTS", "No recipients specified")

    # Security: only allow addresses that belong to this contact.
    allowed_recipients = {addr for addr in [contact.email] if addr}
    allowed_recipients.update(ce.email for ce in contact.emails)
    if invalid := [r for r in payload.recipients if r not in allowed_recipients]:
        raise unprocessable(
            "EMAIL_RECIPIENTS_NOT_ALLOWED",
            f"Recipient(s) not allowed for this contact: {', '.join(invalid)}",
        )

    contact_name = contact.nom
    if contact.prenom:
        contact_name = f"{contact.prenom} {contact.nom}"

    pdf_bytes = pdf_service.generate_invoice_pdf(
        invoice, contact_name, app_settings, contact.adresse
    )

    try:
        email_service.send_invoice_email(
            smtp_host=app_settings.smtp_host or "",
            smtp_port=app_settings.smtp_port,
            smtp_user=app_settings.smtp_user or "",
            smtp_password=app_settings.smtp_password or "",
            smtp_from_email=app_settings.smtp_from_email or "",
            smtp_use_tls=app_settings.smtp_use_tls,
            bcc=app_settings.smtp_bcc,
            recipient_email=payload.recipients,
            invoice_number=invoice.number,
            association_name=app_settings.association_name,
            pdf_bytes=pdf_bytes,
            description=invoice.description,
            override_subject=payload.subject,
            override_body=payload.body,
        )
    except email_service.EmailSendError as exc:
        raise api_error(
            status.HTTP_502_BAD_GATEWAY, "EMAIL_DELIVERY_FAILED", f"Email delivery failed: {exc}"
        ) from exc

    # Auto-transition draft → sent
    from backend.models.invoice import InvoiceStatus  # noqa: PLC0415

    if invoice.status == InvoiceStatus.DRAFT:
        await invoice_service.update_invoice_status(db, invoice, InvoiceStatus.SENT)
    await record_audit(
        db,
        action=AuditAction.INVOICE_EMAIL_SENT,
        actor=current_user,
        target_id=invoice_id,
        target_type="invoice",
        detail={"number": invoice.number, "recipient": contact.email, "subject": payload.subject},
    )


@router.get("/{invoice_id}/file")
async def download_invoice_file(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> FileResponse:
    """Return the uploaded file attachment for a supplier or archived client invoice."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    # Supplier invoices and archived client invoices can have file attachments
    if invoice.type == InvoiceType.CLIENT and invoice.status != InvoiceStatus.ARCHIVED:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "INVOICE_FILE_NOT_AVAILABLE",
            "File download is only available for supplier invoices or archived client invoices",
        )
    if not invoice.file_path:
        raise api_error(status.HTTP_404_NOT_FOUND, "INVOICE_NO_FILE", "No file attached")
    # Resolve absolute path from stored relative filename
    stored = invoice.file_path
    if Path(stored).is_absolute():
        file_path = Path(stored)
    else:
        base = Path("data/uploads/invoices").resolve()
        file_path = (base / stored).resolve()
        if not file_path.is_relative_to(base):
            raise api_error(
                status.HTTP_400_BAD_REQUEST, "INVOICE_INVALID_PATH", "Invalid file path"
            )
    if not file_path.is_file():
        raise api_error(status.HTTP_404_NOT_FOUND, "INVOICE_FILE_MISSING", "File not found on disk")
    suffix = file_path.suffix.lower()
    media_type_map = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    media_type = media_type_map.get(suffix, "application/octet-stream")
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=f"facture_{invoice.number}{suffix}",
    )


@router.post("/{invoice_id}/file", response_model=InvoiceRead)
async def upload_invoice_file(
    invoice_id: int,
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> Invoice:
    """Upload a file attachment for a supplier invoice."""
    invoice = await invoice_service.get_invoice(db, invoice_id)
    if invoice is None:
        raise not_found("Invoice")
    if invoice.type != InvoiceType.FOURNISSEUR:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "INVOICE_FILE_SUPPLIER_ONLY",
            "File upload is only for supplier invoices",
        )

    # Validate content type
    if file.content_type not in _ALLOWED_MIME_TYPES:
        raise api_error(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "INVOICE_FILE_TYPE_NOT_ALLOWED",
            f"File type '{file.content_type}' is not allowed. Use PDF, JPEG, PNG, or WebP.",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise api_error(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "FILE_TOO_LARGE", "File exceeds 10 MB limit"
        )

    # Validate actual file content against magic bytes (not just the client-supplied MIME type)
    if not _content_matches_allowed_type(content):
        raise api_error(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "INVOICE_FILE_CONTENT_INVALID",
            "File content does not match an allowed type (PDF, JPEG, PNG, WebP).",
        )

    # Save with a UUID-based name to prevent path traversal
    suffix = Path(file.filename or "upload").suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    upload_dir = Path("data/uploads/invoices").resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_name
    file_path.write_bytes(content)

    # Store only the relative filename to keep the path portable
    return await invoice_service.set_file_path(db, invoice, safe_name)
