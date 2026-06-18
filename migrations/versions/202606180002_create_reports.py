"""create reports

Revision ID: 202606180002
Revises: 202606180001
Create Date: 2026-06-18 00:02:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202606180002"
down_revision: str | None = "202606180001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("mood_average", sa.Float(), nullable=True),
        sa.Column("mood_min", sa.Integer(), nullable=True),
        sa.Column("mood_max", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("dominant_topics", sa.JSON(), nullable=True),
        sa.Column("positive_patterns", sa.JSON(), nullable=True),
        sa.Column("negative_patterns", sa.JSON(), nullable=True),
        sa.Column("key_events", sa.JSON(), nullable=True),
        sa.Column("lessons_learned", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "report_type",
            "period_start",
            "period_end",
            name="uq_reports_user_type_period",
        ),
    )
    op.create_index("ix_reports_period_end", "reports", ["period_end"])
    op.create_index("ix_reports_period_start", "reports", ["period_start"])
    op.create_index("ix_reports_report_type", "reports", ["report_type"])
    op.create_index("ix_reports_user_id", "reports", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_user_id", table_name="reports")
    op.drop_index("ix_reports_report_type", table_name="reports")
    op.drop_index("ix_reports_period_start", table_name="reports")
    op.drop_index("ix_reports_period_end", table_name="reports")
    op.drop_table("reports")
