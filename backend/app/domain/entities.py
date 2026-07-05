from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

DependencyType = Literal["finish_to_start"]


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    plan_id: str
    name: str
    duration_days: int
    position: int = 0
    description: str = ""
    assignee: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TaskDependency:
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: DependencyType = "finish_to_start"


@dataclass(frozen=True, slots=True)
class Plan:
    id: str
    name: str
    start_date: date
    version: int = 1
    tasks: tuple[Task, ...] = ()
    dependencies: tuple[TaskDependency, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
