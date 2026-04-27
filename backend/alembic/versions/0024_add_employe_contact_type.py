"""Add 'employe' value to contact type.

The contacts.type column is a String(20) — no DDL change is needed.
This migration documents the new valid enum value EMPLOYE = "employe"
introduced alongside the employee management feature (BIZ-088).

Revision ID: 0024
Revises: 0023
Create Date: 2026-05-10
"""

from collections.abc import Sequence

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # contacts.type is VARCHAR(20) — the new enum value 'employe' fits without DDL change.
    pass


def downgrade() -> None:
    # Rows with type='employe' would need to be reassigned before downgrading.
    pass
