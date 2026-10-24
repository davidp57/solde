"""Document service — store, list and remove free-form documents.

Only metadata reaches the database; the bytes are written under ``data/documents/``.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from backend.models.document import Document
from backend.models.fiscal_year import FiscalYear
from backend.schemas.document import DocumentRead, DocumentTagRead, DocumentUpdate

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence

DOCUMENTS_DIR = Path("data/documents")

#: Largest file accepted, in bytes. A scanned set of minutes outweighs a spreadsheet,
#: hence twice the Excel-import ceiling.
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_STORED_NAME = 120

#: Header bytes that identify an accepted format. Checked instead of the declared
#: Content-Type, which the client chooses freely, and instead of the extension alone,
#: which renaming defeats.
_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"%PDF", "application/pdf"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"PK\x03\x04", "application/zip"),  # xlsx, docx, odt… — all ZIP containers
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "application/vnd.ms-office"),  # legacy xls/doc
)

#: Formats with no signature of their own, accepted on extension once the content is
#: shown to be text.
_TEXT_EXTENSIONS = (".csv", ".txt", ".md", ".json", ".xml", ".log")

_TEXT_MIME_TYPES = {
    ".csv": "text/csv",
    ".md": "text/markdown",
    ".json": "application/json",
    ".xml": "application/xml",
}

ACCEPTED_FORMATS = "PDF, JPEG, PNG, WebP, Excel, Word, CSV, Markdown, texte"


class DocumentError(ValueError):
    """Raised when a document cannot be accepted, carrying a machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def normalize_tags(raw: Sequence[str] | None) -> list[str]:
    """Lower-case, collapse whitespace, drop blanks and duplicates, keep first order.

    Without this, "AG" and "ag" coexist and no filter ever matches both.
    """
    seen: list[str] = []
    for item in raw or []:
        tag = re.sub(r"\s+", " ", item).strip().lower()
        if tag and tag not in seen:
            seen.append(tag)
    return seen


def parse_tags(raw: str | None) -> list[str]:
    """Read the comma-separated tag field sent by the form."""
    return normalize_tags((raw or "").split(","))


def detect_mime_type(content: bytes, filename: str) -> str:
    """Return the MIME type of an accepted file, or refuse it.

    A WebP file is a RIFF container whose type marker sits at offset 8, so it is
    checked apart from the leading-bytes table.
    """
    if not content:
        raise DocumentError("DOCUMENT_EMPTY", "Le fichier est vide.")

    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"

    for signature, mime in _SIGNATURES:
        if content.startswith(signature):
            return mime

    suffix = Path(filename).suffix.lower()
    if suffix in _TEXT_EXTENSIONS and _looks_like_text(content):
        return _TEXT_MIME_TYPES.get(suffix, "text/plain")

    raise DocumentError(
        "DOCUMENT_INVALID_TYPE",
        f"Format de fichier non pris en charge. Formats acceptés : {ACCEPTED_FORMATS}.",
    )


def _looks_like_text(content: bytes) -> bool:
    """Report whether the bytes decode as text, so a renamed binary is not let through."""
    if b"\x00" in content[:4096]:
        return False
    for encoding in ("utf-8", "latin-1"):
        try:
            content[:4096].decode(encoding)
        except UnicodeDecodeError:
            continue
        else:
            return True
    return False


def _safe_stored_name(filename: str) -> str:
    """Build a collision-free storage name that cannot escape the documents directory.

    Only the final component is kept, so a name carrying ``../`` or a separator lands
    inside ``data/documents/`` like any other.
    """
    bare = Path(filename.replace("\\", "/")).name
    cleaned = _SAFE_NAME.sub("-", bare).strip("-.") or "document"
    return f"{uuid.uuid4().hex}-{cleaned[:_MAX_STORED_NAME]}"


async def _to_read(db: AsyncSession, document: Document) -> DocumentRead:
    """Build the DTO, resolving the fiscal-year name when there is one."""
    name: str | None = None
    if document.fiscal_year_id is not None:
        name = (
            await db.execute(
                select(FiscalYear.name).where(FiscalYear.id == document.fiscal_year_id)
            )
        ).scalar_one_or_none()
    return DocumentRead.model_validate(document).model_copy(update={"fiscal_year_name": name})


async def store_document(
    db: AsyncSession,
    *,
    title: str,
    filename: str,
    content: bytes,
    fiscal_year_id: int | None = None,
    tags: Sequence[str] | None = None,
    notes: str | None = None,
    uploaded_by: str | None = None,
) -> DocumentRead:
    """Validate, write to disk and record a document."""
    title = title.strip()
    if not title:
        raise DocumentError("DOCUMENT_TITLE_REQUIRED", "Le titre est obligatoire.")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentError(
            "FILE_TOO_LARGE",
            f"Fichier trop volumineux (limite : {MAX_DOCUMENT_BYTES // (1024 * 1024)} Mo).",
        )

    # Validate before writing: a refused file must leave nothing behind.
    mime_type = detect_mime_type(content, filename)

    if fiscal_year_id is not None:
        exists = await db.get(FiscalYear, fiscal_year_id)
        if exists is None:
            raise DocumentError("FISCAL_YEAR_NOT_FOUND", "Exercice introuvable.")

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = DOCUMENTS_DIR / _safe_stored_name(filename)
    stored_path.write_bytes(content)

    document = Document(
        title=title,
        filename=Path(filename.replace("\\", "/")).name or "document",
        stored_path=str(stored_path),
        mime_type=mime_type,
        size_bytes=len(content),
        fiscal_year_id=fiscal_year_id,
        tags=normalize_tags(tags),
        notes=notes,
        uploaded_by=uploaded_by,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return await _to_read(db, document)


async def get_document(db: AsyncSession, document_id: int) -> DocumentRead | None:
    document = await db.get(Document, document_id)
    return None if document is None else await _to_read(db, document)


async def list_documents(
    db: AsyncSession,
    *,
    fiscal_year_id: int | None = None,
    without_fiscal_year: bool = False,
    tag: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[DocumentRead], int]:
    """Return a page of documents, most recently uploaded first, and the total count."""
    query = select(Document)
    count_query = select(func.count()).select_from(Document)

    filters: list[ColumnElement[bool]] = []
    if without_fiscal_year:
        filters.append(Document.fiscal_year_id.is_(None))
    elif fiscal_year_id is not None:
        filters.append(Document.fiscal_year_id == fiscal_year_id)
    if search:
        pattern = f"%{search}%"
        filters.append(
            or_(
                Document.title.ilike(pattern),
                Document.notes.ilike(pattern),
                Document.filename.ilike(pattern),
            )
        )
    for condition in filters:
        query = query.where(condition)
        count_query = count_query.where(condition)

    query = query.order_by(Document.uploaded_at.desc(), Document.id.desc())
    rows = list((await db.execute(query)).scalars().all())

    # Tag matching happens in Python: the column is a JSON list, and SQLite offers no
    # portable containment operator for it. The collection stays small enough that the
    # cost is irrelevant.
    if tag:
        wanted = normalize_tags([tag])
        rows = [row for row in rows if wanted and wanted[0] in (row.tags or [])]
        total = len(rows)
    else:
        total = (await db.execute(count_query)).scalar_one()

    page = rows[offset : offset + limit]
    return [await _to_read(db, row) for row in page], total


async def list_tags(db: AsyncSession) -> list[DocumentTagRead]:
    """Return the tags in use with their occurrence count, most used first."""
    rows = list((await db.execute(select(Document.tags))).scalars().all())
    counts: dict[str, int] = {}
    for tags in rows:
        for tag in tags or []:
            counts[tag] = counts.get(tag, 0) + 1
    return [
        DocumentTagRead(tag=tag, count=count)
        for tag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


async def update_document(
    db: AsyncSession, document_id: int, payload: DocumentUpdate
) -> DocumentRead | None:
    """Update the editable metadata of a document."""
    document = await db.get(Document, document_id)
    if document is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            raise DocumentError("DOCUMENT_TITLE_REQUIRED", "Le titre est obligatoire.")
        document.title = title
    if "fiscal_year_id" in data:
        fiscal_year_id = data["fiscal_year_id"]
        if fiscal_year_id is not None and await db.get(FiscalYear, fiscal_year_id) is None:
            raise DocumentError("FISCAL_YEAR_NOT_FOUND", "Exercice introuvable.")
        document.fiscal_year_id = fiscal_year_id
    if "tags" in data:
        document.tags = normalize_tags(data["tags"])
    if "notes" in data:
        document.notes = data["notes"]

    await db.flush()
    await db.refresh(document)
    return await _to_read(db, document)


async def delete_document(db: AsyncSession, document_id: int) -> bool:
    """Delete a document and its file. A file already gone does not block the deletion."""
    document = await db.get(Document, document_id)
    if document is None:
        return False

    Path(document.stored_path).unlink(missing_ok=True)
    await db.delete(document)
    await db.flush()
    return True


async def get_document_file(db: AsyncSession, document_id: int) -> tuple[Path, str, str] | None:
    """Return (path, original filename, mime type) for a download, or None."""
    document = await db.get(Document, document_id)
    if document is None:
        return None
    path = Path(document.stored_path)
    if not path.is_file():
        raise DocumentError(
            "DOCUMENT_FILE_MISSING",
            "Le fichier est introuvable sur le serveur.",
        )
    return path, document.filename, document.mime_type or "application/octet-stream"
