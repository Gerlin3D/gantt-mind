from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class PlanModel(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    tasks: Mapped[list["TaskModel"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TaskModel.position, TaskModel.id",
    )


class TaskModel(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("duration_days > 0", name="ck_tasks_duration_positive"),
        UniqueConstraint("plan_id", "position", name="uq_tasks_plan_position"),
        Index("ix_tasks_plan_id", "plan_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    plan_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    assignee: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_days: Mapped[int] = mapped_column(nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    position: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    plan: Mapped[PlanModel] = relationship(back_populates="tasks")
    predecessor_dependencies: Mapped[list["TaskDependencyModel"]] = relationship(
        foreign_keys="TaskDependencyModel.predecessor_task_id",
        back_populates="predecessor_task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    successor_dependencies: Mapped[list["TaskDependencyModel"]] = relationship(
        foreign_keys="TaskDependencyModel.successor_task_id",
        back_populates="successor_task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TaskDependencyModel(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        CheckConstraint(
            "dependency_type = 'finish_to_start'",
            name="ck_task_dependencies_type_finish_to_start",
        ),
        CheckConstraint(
            "predecessor_task_id <> successor_task_id",
            name="ck_task_dependencies_no_self_dependency",
        ),
        Index("ix_task_dependencies_predecessor_task_id", "predecessor_task_id"),
        Index("ix_task_dependencies_successor_task_id", "successor_task_id"),
    )

    predecessor_task_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    successor_task_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dependency_type: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default="finish_to_start",
    )

    predecessor_task: Mapped[TaskModel] = relationship(
        foreign_keys=[predecessor_task_id],
        back_populates="predecessor_dependencies",
    )
    successor_task: Mapped[TaskModel] = relationship(
        foreign_keys=[successor_task_id],
        back_populates="successor_dependencies",
    )
