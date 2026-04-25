"""Add index on invoices.due_date for overdue filter performance.

Revision ID: 0028
Revises: 0027
Create Date: 2026-04-25
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_invoices_due_date", "invoices", ["due_date"])


def downgrade() -> None:
    op.drop_index("ix_invoices_due_date", table_name="invoices")
