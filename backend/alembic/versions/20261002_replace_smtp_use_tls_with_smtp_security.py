"""replace smtp_use_tls with an explicit smtp_security mode

The boolean was read differently by the send paths. Existing values are
translated to the meaning the invoice send path already applied:
True -> "starttls", False -> "ssl".

Revision ID: e3a9c5d1f702
Revises: c7d2f1a34b90
Create Date: 2026-10-02 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3a9c5d1f702"
down_revision: str | None = "c7d2f1a34b90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "smtp_security", sa.String(length=10), nullable=False, server_default="starttls"
            )
        )
    op.execute(
        "UPDATE app_settings SET smtp_security = "
        "CASE WHEN smtp_use_tls THEN 'starttls' ELSE 'ssl' END"
    )
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("smtp_use_tls")


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column("smtp_use_tls", sa.Boolean(), nullable=False, server_default=sa.true())
        )
    # "none" has no boolean equivalent; it maps to the STARTTLS side.
    op.execute("UPDATE app_settings SET smtp_use_tls = (smtp_security != 'ssl')")
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("smtp_security")
