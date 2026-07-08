from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.application.change_set_service import (
    AddDependencyChange,
    ChangeAssigneeChange,
    ChangeDurationChange,
    ChangeOperation,
    RemoveDependencyChange,
    ShiftTasksChange,
)
from app.domain.entities import Plan

ALLOWED_AI_OPERATIONS = (
    "shift_tasks",
    "change_duration",
    "change_assignee",
    "add_dependency",
    "remove_dependency",
)


class StrictAiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ShiftTasksOperation(StrictAiModel):
    type: Literal["shift_tasks"]
    task_ids: list[str] = Field(min_length=1)
    offset_days: int


class ChangeDurationOperation(StrictAiModel):
    type: Literal["change_duration"]
    task_id: str = Field(min_length=1)
    duration_days: int


class ChangeAssigneeOperation(StrictAiModel):
    type: Literal["change_assignee"]
    task_ids: list[str] = Field(min_length=1)
    assignee: str | None = None


class AddDependencyOperation(StrictAiModel):
    type: Literal["add_dependency"]
    predecessor_task_id: str = Field(min_length=1)
    successor_task_id: str = Field(min_length=1)


class RemoveDependencyOperation(StrictAiModel):
    type: Literal["remove_dependency"]
    predecessor_task_id: str = Field(min_length=1)
    successor_task_id: str = Field(min_length=1)


AiOperation = Annotated[
    ShiftTasksOperation
    | ChangeDurationOperation
    | ChangeAssigneeOperation
    | AddDependencyOperation
    | RemoveDependencyOperation,
    Field(discriminator="type"),
]


class AiOperationProposal(StrictAiModel):
    change_summary: str = Field(min_length=1)
    operations: list[AiOperation] = Field(default_factory=list)


def ai_operation_to_change(operation: AiOperation) -> ChangeOperation:
    if isinstance(operation, ShiftTasksOperation):
        return ShiftTasksChange(
            type="shift_tasks",
            task_ids=tuple(operation.task_ids),
            offset_days=operation.offset_days,
        )
    if isinstance(operation, ChangeDurationOperation):
        return ChangeDurationChange(
            type="change_duration",
            task_id=operation.task_id,
            duration_days=operation.duration_days,
        )
    if isinstance(operation, ChangeAssigneeOperation):
        normalized_assignee = operation.assignee.strip() if operation.assignee else None
        return ChangeAssigneeChange(
            type="change_assignee",
            task_ids=tuple(operation.task_ids),
            assignee=normalized_assignee or None,
        )
    if isinstance(operation, AddDependencyOperation):
        return AddDependencyChange(
            type="add_dependency",
            predecessor_task_id=operation.predecessor_task_id,
            successor_task_id=operation.successor_task_id,
        )
    return RemoveDependencyChange(
        type="remove_dependency",
        predecessor_task_id=operation.predecessor_task_id,
        successor_task_id=operation.successor_task_id,
    )


def referenced_task_ids(operation: AiOperation) -> set[str]:
    if isinstance(operation, ShiftTasksOperation | ChangeAssigneeOperation):
        return set(operation.task_ids)
    if isinstance(operation, ChangeDurationOperation):
        return {operation.task_id}
    return {operation.predecessor_task_id, operation.successor_task_id}


def build_plan_context(plan: Plan) -> dict[str, object]:
    return {
        "plan_id": plan.id,
        "plan_name": plan.name,
        "version": plan.version,
        "tasks": [
            {
                "id": task.id,
                "name": task.name,
                "assignee": task.assignee,
                "duration_days": task.duration_days,
                "start_date": task.start_date.isoformat() if task.start_date else None,
                "end_date": task.end_date.isoformat() if task.end_date else None,
            }
            for task in plan.tasks
        ],
        "dependencies": [
            {
                "predecessor_task_id": dependency.predecessor_task_id,
                "successor_task_id": dependency.successor_task_id,
            }
            for dependency in plan.dependencies
        ],
    }
