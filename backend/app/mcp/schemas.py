from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.application.change_set_service import (
    AddDependencyChange,
    ChangeAssigneeChange,
    ChangeDurationChange,
    ChangeOperation,
    DeleteTaskChange,
    RemoveDependencyChange,
    ShiftTasksChange,
)
from app.domain.entities import Plan, Task, TaskDependency


class StrictMcpModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class McpErrorPayload(StrictMcpModel):
    code: str
    message: str
    details: dict[str, object] | None = None


class McpResult(StrictMcpModel):
    ok: bool
    data: dict[str, object] | None = None
    error: McpErrorPayload | None = None


class GetPlanSnapshotInput(StrictMcpModel):
    plan_id: str = Field(min_length=1)


class FindTasksInput(StrictMcpModel):
    plan_id: str = Field(min_length=1)
    query: str | None = None
    assignee: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class ValidatePlanInput(StrictMcpModel):
    plan_id: str = Field(min_length=1)


class ShiftTasksInput(StrictMcpModel):
    type: Literal["shift_tasks"]
    task_ids: list[str] = Field(min_length=1)
    offset_days: int


class ChangeDurationInput(StrictMcpModel):
    type: Literal["change_duration"]
    task_id: str = Field(min_length=1)
    duration_days: int


class ChangeAssigneeInput(StrictMcpModel):
    type: Literal["change_assignee"]
    task_ids: list[str] = Field(min_length=1)
    assignee: str | None = None


class AddDependencyInput(StrictMcpModel):
    type: Literal["add_dependency"]
    predecessor_task_id: str = Field(min_length=1)
    successor_task_id: str = Field(min_length=1)


class RemoveDependencyInput(StrictMcpModel):
    type: Literal["remove_dependency"]
    predecessor_task_id: str = Field(min_length=1)
    successor_task_id: str = Field(min_length=1)


class DeleteTaskInput(StrictMcpModel):
    type: Literal["delete_task"]
    task_id: str = Field(min_length=1)


ChangeOperationInput = Annotated[
    ShiftTasksInput
    | ChangeDurationInput
    | ChangeAssigneeInput
    | AddDependencyInput
    | RemoveDependencyInput
    | DeleteTaskInput,
    Field(discriminator="type"),
]


class ApplyChangeSetInput(StrictMcpModel):
    plan_id: str = Field(min_length=1)
    expected_version: int = Field(ge=1)
    operations: list[ChangeOperationInput] = Field(min_length=1)
    user_request: str | None = None


def operation_input_to_application(operation: ChangeOperationInput) -> ChangeOperation:
    if isinstance(operation, ShiftTasksInput):
        return ShiftTasksChange(
            type="shift_tasks",
            task_ids=tuple(operation.task_ids),
            offset_days=operation.offset_days,
        )
    if isinstance(operation, ChangeDurationInput):
        return ChangeDurationChange(
            type="change_duration",
            task_id=operation.task_id,
            duration_days=operation.duration_days,
        )
    if isinstance(operation, ChangeAssigneeInput):
        normalized_assignee = operation.assignee.strip() if operation.assignee else None
        return ChangeAssigneeChange(
            type="change_assignee",
            task_ids=tuple(operation.task_ids),
            assignee=normalized_assignee or None,
        )
    if isinstance(operation, AddDependencyInput):
        return AddDependencyChange(
            type="add_dependency",
            predecessor_task_id=operation.predecessor_task_id,
            successor_task_id=operation.successor_task_id,
        )
    if isinstance(operation, RemoveDependencyInput):
        return RemoveDependencyChange(
            type="remove_dependency",
            predecessor_task_id=operation.predecessor_task_id,
            successor_task_id=operation.successor_task_id,
        )
    return DeleteTaskChange(type="delete_task", task_id=operation.task_id)


def task_to_payload(task: Task) -> dict[str, object]:
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "assignee": task.assignee,
        "duration_days": task.duration_days,
        "start_date": task.start_date.isoformat() if task.start_date else None,
        "end_date": task.end_date.isoformat() if task.end_date else None,
        "position": task.position,
    }


def dependency_to_payload(dependency: TaskDependency) -> dict[str, object]:
    return {
        "predecessor_task_id": dependency.predecessor_task_id,
        "successor_task_id": dependency.successor_task_id,
        "dependency_type": dependency.dependency_type,
    }


def plan_to_payload(plan: Plan) -> dict[str, object]:
    return {
        "id": plan.id,
        "name": plan.name,
        "start_date": plan.start_date.isoformat(),
        "version": plan.version,
        "tasks": [task_to_payload(task) for task in plan.tasks],
        "dependencies": [dependency_to_payload(dependency) for dependency in plan.dependencies],
    }
