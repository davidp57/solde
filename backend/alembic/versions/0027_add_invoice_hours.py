"""Add hours column to invoices table for freelance contractor cost tracking.

Optional field — only populated for supplier invoices from auto-entrepreneurs
to enable hourly cost comparison in the workforce cost view (BIZ-089).

Revision ID: 0027
Revises: 0026
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("hours", sa.Numeric(8, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("invoices", "hours")
