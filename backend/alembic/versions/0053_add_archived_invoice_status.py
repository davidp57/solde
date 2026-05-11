"""Add ARCHIVED invoice status.

Both InvoiceStatus values are stored as VARCHAR strings in SQLite — no schema change
is needed. This migration serves as a documentation marker for the feature
introduced in BIZ-187 (Lot FW — Import Word + Archivage + Export Excel).

Revision ID: 0053
Revises: 0052
Create Date: 2026-05-11
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0053"
down_revision: str | None = "0052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # No schema change required: InvoiceStatus is stored as VARCHAR.
    pass


def downgrade() -> None:
    pass
