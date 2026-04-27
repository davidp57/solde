"""Add ON DELETE CASCADE to payments.invoice_id FK.

SQLite does not support ALTER TABLE ADD/DROP CONSTRAINT, so we recreate
the payments table with the new FK constraint.

The original FK was created in migration 0005 without an explicit name, so
its reflected name is unknown at write time.  We use SQLAlchemy inspection at
run time to locate the correct constraint before dropping it.

Revision ID: 0030
Revises: 0029
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _invoice_fk_name() -> str | None:
    """Return the reflected name of the FK payments.invoice_id → invoices.id."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return next(
        (
            fk.get("name")
            for fk in inspector.get_foreign_keys("payments")
            if fk.get("referred_table") == "invoices"
            and "invoice_id" in (fk.get("constrained_columns") or [])
        ),
        None,
    )


def upgrade() -> None:
    old_fk_name = _invoice_fk_name()
    with op.batch_alter_table("payments", recreate="always") as batch_op:
        if old_fk_name is not None:
            batch_op.drop_constraint(old_fk_name, type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_payments_invoice_id",
            "invoices",
            ["invoice_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("payments", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_payments_invoice_id", type_="foreignkey")
        # Recreate without CASCADE, unnamed (matching the original migration 0005)
        batch_op.create_foreign_key(
            None,
            "invoices",
            ["invoice_id"],
            ["id"],
        )
