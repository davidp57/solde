"""Backup destination model — stores rclone-based backup targets."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class BackupDestination(Base):
    """A backup destination configured by the admin.

    Each destination maps to an rclone remote. Supported types:
    - ``local``: local filesystem path
    - ``smb``: SMB/CIFS share
    - ``onedrive``: Microsoft OneDrive (OAuth2 via rclone)
    """

    __tablename__ = "backup_destination"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # local | smb | onedrive
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rclone_remote_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rclone_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    target_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
