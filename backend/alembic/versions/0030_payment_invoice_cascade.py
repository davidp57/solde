"""Add ON DELETE CASCADE to payments.invoice_id FK.

SQLite does not support ALTER TABLE ADD/DROP CONSTRAINT, so we recreate
the payments table with the new FK constraint.

Revision ID: 0030
Revises: 0029
Create Date: 2026-04-29
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("payments", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_payments_invoice_id", type_="foreignkey")
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
        batch_op.create_foreign_key(
            "fk_payments_invoice_id",
            "invoices",
            ["invoice_id"],
            ["id"],
        )
