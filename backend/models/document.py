"""Document model — free-form file storage, optionally tied to a fiscal year."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Document(Base):
    """A file kept for the record, with a human title and free-form tags.

    Deliberately detached from invoices, payments and salaries: the point is to hold
    what has no natural owner — statutes, minutes, insurance certificates, signed
    financial statements. Only metadata lives here; the bytes stay on disk.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # A deleted fiscal year must not take its documents with it: the statutes outlive
    # every accounting period, and so does a signed balance sheet.
    fiscal_year_id: Mapped[int | None] = mapped_column(
        ForeignKey("fiscal_years.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default=text("'[]'")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
