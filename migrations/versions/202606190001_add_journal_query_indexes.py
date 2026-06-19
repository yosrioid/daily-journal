"""add journal query indexes

Revision ID: 202606190001
Revises: 202606180002
Create Date: 2026-06-19 10:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202606190001"
down_revision: str | None = "202606180002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_journal_entries_user_entry_date_created_at",
        "journal_entries",
        ["user_id", "entry_date", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_journal_entries_user_entry_date_created_at",
        table_name="journal_entries",
    )
