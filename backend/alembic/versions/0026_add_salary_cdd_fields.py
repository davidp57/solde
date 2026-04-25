"""Add CDD breakdown columns to salaries table.

Adds brut_declared, conges_payes, precarite — nullable columns to store the
individual components of a CDD salary before CEA calculation (BIZ-089).

Revision ID: 0026
Revises: 0025
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("salaries", sa.Column("brut_declared", sa.Numeric(10, 2), nullable=True))
    op.add_column("salaries", sa.Column("conges_payes", sa.Numeric(10, 2), nullable=True))
    op.add_column("salaries", sa.Column("precarite", sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("salaries", "precarite")
    op.drop_column("salaries", "conges_payes")
    op.drop_column("salaries", "brut_declared")
