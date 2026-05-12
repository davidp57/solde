"""Merge archived invoice status and list default limit branches.

Revision ID: 9f4d2a1c6b7e
Revises: 0054, b5c2d4e1f023
Create Date: 2026-05-12 00:00:00.000000
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "9f4d2a1c6b7e"
down_revision: str | tuple[str, str] | None = ("0054", "b5c2d4e1f023")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
