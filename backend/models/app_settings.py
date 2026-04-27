"""Application settings model — single-row table (id always = 1)."""

from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class AppSettings(Base):
    """Application-wide settings persisted in the database.

    Only one row exists (id=1). Use the settings service to read/write.
    """

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Association info (printed on invoices)
    association_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Mon Association"
    )
    association_address: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    association_siret: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    association_logo_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # Fiscal year (month number: 8 = August)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    default_invoice_due_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Invoice numbering
    client_invoice_seq_digits: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    client_invoice_number_template: Mapped[str] = mapped_column(
        String(100), nullable=False, default="{year}-{seq}"
    )
    supplier_invoice_number_template: Mapped[str] = mapped_column(
        String(100), nullable=False, default="FF-%Y%m%d%H.%M.%S"
    )

    # Default unit prices per invoice line type (null = no default)
    default_price_cours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    default_price_adhesion: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    default_price_autres: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # SMTP (all optional)
    smtp_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    smtp_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    smtp_bcc: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Chat / AI assistant
    chat_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="gemini")
    chat_api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    chat_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
