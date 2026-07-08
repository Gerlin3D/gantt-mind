"""create change sets

Revision ID: 0002_create_change_sets
Revises: 0001_create_plan_tables
Create Date: 2026-07-08
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_create_change_sets"
down_revision: str | None = "0001_create_plan_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "change_sets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("plan_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("user_request", sa.String(length=2000), nullable=True),
        sa.Column("operations", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_change_sets_plan_id", "change_sets", ["plan_id"], unique=False)
    op.create_index("ix_change_sets_created_at", "change_sets", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_change_sets_created_at", table_name="change_sets")
    op.drop_index("ix_change_sets_plan_id", table_name="change_sets")
    op.drop_table("change_sets")
