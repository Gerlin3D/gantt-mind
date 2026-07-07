"""create plan tables

Revision ID: 0001_create_plan_tables
Revises: None
Create Date: 2026-07-06
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_create_plan_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("plan_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("assignee", sa.String(length=255), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("duration_days > 0", name="ck_tasks_duration_positive"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id", "position", name="uq_tasks_plan_position"),
    )
    op.create_index("ix_tasks_plan_id", "tasks", ["plan_id"], unique=False)
    op.create_table(
        "task_dependencies",
        sa.Column("predecessor_task_id", sa.String(length=64), nullable=False),
        sa.Column("successor_task_id", sa.String(length=64), nullable=False),
        sa.Column("dependency_type", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "dependency_type = 'finish_to_start'",
            name="ck_task_dependencies_type_finish_to_start",
        ),
        sa.CheckConstraint(
            "predecessor_task_id <> successor_task_id",
            name="ck_task_dependencies_no_self_dependency",
        ),
        sa.ForeignKeyConstraint(["predecessor_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["successor_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint(
            "predecessor_task_id",
            "successor_task_id",
            "dependency_type",
        ),
    )
    op.create_index(
        "ix_task_dependencies_predecessor_task_id",
        "task_dependencies",
        ["predecessor_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_task_dependencies_successor_task_id",
        "task_dependencies",
        ["successor_task_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_task_dependencies_successor_task_id", table_name="task_dependencies")
    op.drop_index("ix_task_dependencies_predecessor_task_id", table_name="task_dependencies")
    op.drop_table("task_dependencies")
    op.drop_index("ix_tasks_plan_id", table_name="tasks")
    op.drop_table("tasks")
    op.drop_table("plans")
