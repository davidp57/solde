"""Add contract fields to contacts table for employee management.

Adds contract_type, base_gross, base_hours, hourly_rate, is_contractor columns
to support CDI/CDD distinction and freelance contractor tracking (BIZ-089).

Revision ID: 0025
Revises: 0024
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("contract_type", sa.String(10), nullable=True))
    op.add_column("contacts", sa.Column("base_gross", sa.Numeric(10, 2), nullable=True))
    op.add_column("contacts", sa.Column("base_hours", sa.Numeric(8, 2), nullable=True))
    op.add_column("contacts", sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=True))
    op.add_column(
        "contacts",
        sa.Column("is_contractor", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("contacts", "is_contractor")
    op.drop_column("contacts", "hourly_rate")
    op.drop_column("contacts", "base_hours")
    op.drop_column("contacts", "base_gross")
    op.drop_column("contacts", "contract_type")
