"""Add IRRECOVERABLE invoice status and WRITE_OFF entry source type.

Both values are stored as VARCHAR strings in SQLite — no schema change is needed.
This migration serves as a documentation marker for the feature introduced in BIZ-113.

Revision ID: 0031
Revises: 0030
Create Date: 2026-05-05
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # No schema change required: InvoiceStatus and EntrySourceType are stored as VARCHAR.
    pass


def downgrade() -> None:
    pass
