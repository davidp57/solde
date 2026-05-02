"""Migration 0047 — add contact_emails table.

Stores up to 2 additional email addresses per contact (max 3 total
including the primary contact.email field).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0047"
down_revision: str = "0046"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contact_emails",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "contact_id",
            sa.Integer(),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("label", sa.String(50), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_contact_emails_id", "contact_emails", ["id"], unique=False)
    op.create_index("ix_contact_emails_contact_id", "contact_emails", ["contact_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_contact_emails_contact_id", table_name="contact_emails")
    op.drop_index("ix_contact_emails_id", table_name="contact_emails")
    op.drop_table("contact_emails")
