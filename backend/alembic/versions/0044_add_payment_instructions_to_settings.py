"""Migration 0044 — add payment instruction fields to app_settings.

Adds three nullable columns used to print payment instructions on client invoices:
  payment_iban        — IBAN of the association's bank account
  payment_bic         — BIC/SWIFT code of the bank
  payment_check_payee — payee name for cheque payments
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0044"
down_revision: str = "0043"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(sa.Column("payment_iban", sa.String(34), nullable=True))
        batch_op.add_column(sa.Column("payment_bic", sa.String(11), nullable=True))
        batch_op.add_column(sa.Column("payment_check_payee", sa.String(255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("payment_check_payee")
        batch_op.drop_column("payment_bic")
        batch_op.drop_column("payment_iban")
