from dataclasses import asdict, dataclass, replace
from typing import Literal
from uuid import uuid4

from app.application.change_set_repository import ChangeSetRepository
from app.application.exceptions import (
    InvalidChangeSetError,
    PlanNotFoundError,
    PlanVersionConflictError,
)
from app.application.plan_repository import PlanRepository
from app.domain.entities import ChangeSet, Plan
from app.domain.operations import (
    add_finish_to_start_dependency,
    change_task_assignee,
    change_task_duration,
    delete_task,
    remove_finish_to_start_dependency,
    shift_tasks,
)
from app.domain.scheduler import schedule_plan


@dataclass(frozen=True, slots=True)
class ShiftTasksChange:
    type: Literal["shift_tasks"]
    task_ids: tuple[str, ...]
    offset_days: int


@dataclass(frozen=True, slots=True)
class ChangeDurationChange:
    type: Literal["change_duration"]
    task_id: str
    duration_days: int


@dataclass(frozen=True, slots=True)
class ChangeAssigneeChange:
    type: Literal["change_assignee"]
    task_ids: tuple[str, ...]
    assignee: str | None


@dataclass(frozen=True, slots=True)
class AddDependencyChange:
    type: Literal["add_dependency"]
    predecessor_task_id: str
    successor_task_id: str


@dataclass(frozen=True, slots=True)
class RemoveDependencyChange:
    type: Literal["remove_dependency"]
    predecessor_task_id: str
    successor_task_id: str


@dataclass(frozen=True, slots=True)
class DeleteTaskChange:
    type: Literal["delete_task"]
    task_id: str


ChangeOperation = (
    ShiftTasksChange
    | ChangeDurationChange
    | ChangeAssigneeChange
    | AddDependencyChange
    | RemoveDependencyChange
    | DeleteTaskChange
)


@dataclass(frozen=True, slots=True)
class AppliedChangeSet:
    change_set: ChangeSet
    plan: Plan
    applied_operations: tuple[ChangeOperation, ...]
    description: str


class ChangeSetService:
    def __init__(
        self,
        plan_repository: PlanRepository,
        change_set_repository: ChangeSetRepository,
    ) -> None:
        self._plan_repository = plan_repository
        self._change_set_repository = change_set_repository

    def apply_change_set(
        self,
        *,
        plan_id: str,
        expected_version: int,
        operations: tuple[ChangeOperation, ...],
        source: str = "mcp",
        user_request: str | None = None,
    ) -> AppliedChangeSet:
        if expected_version < 1:
            raise InvalidChangeSetError("expected_version must be a positive integer.")
        if not operations:
            raise InvalidChangeSetError("operations must contain at least one operation.")

        plan = self._plan_repository.get_snapshot(plan_id)
        if plan is None:
            raise PlanNotFoundError(plan_id)
        if plan.version != expected_version:
            raise PlanVersionConflictError(plan_id, expected_version, plan.version)

        updated_plan = schedule_plan(plan)
        for operation in operations:
            updated_plan = self._apply_operation(updated_plan, operation)

        updated_plan = replace(updated_plan, version=plan.version + 1)
        saved_plan = self._plan_repository.replace(updated_plan)
        change_set = ChangeSet(
            id=f"changeset-{uuid4().hex[:12]}",
            plan_id=plan_id,
            source=source,
            user_request=user_request,
            operations=tuple(_operation_to_record(operation) for operation in operations),
        )
        saved_change_set = self._change_set_repository.save(change_set)

        return AppliedChangeSet(
            change_set=saved_change_set,
            plan=saved_plan,
            applied_operations=operations,
            description=_describe_operations(operations),
        )

    def _apply_operation(self, plan: Plan, operation: ChangeOperation) -> Plan:
        if isinstance(operation, ShiftTasksChange):
            return shift_tasks(plan, operation.task_ids, operation.offset_days)
        if isinstance(operation, ChangeDurationChange):
            return change_task_duration(plan, operation.task_id, operation.duration_days)
        if isinstance(operation, ChangeAssigneeChange):
            return change_task_assignee(plan, operation.task_ids, operation.assignee)
        if isinstance(operation, AddDependencyChange):
            return add_finish_to_start_dependency(
                plan,
                operation.predecessor_task_id,
                operation.successor_task_id,
            )
        if isinstance(operation, RemoveDependencyChange):
            return remove_finish_to_start_dependency(
                plan,
                operation.predecessor_task_id,
                operation.successor_task_id,
            )
        if isinstance(operation, DeleteTaskChange):
            return delete_task(plan, operation.task_id)


def _operation_to_record(operation: ChangeOperation) -> dict[str, object]:
    return asdict(operation)


def _describe_operations(operations: tuple[ChangeOperation, ...]) -> str:
    counts_by_type: dict[str, int] = {}
    for operation in operations:
        counts_by_type[operation.type] = counts_by_type.get(operation.type, 0) + 1
    return ", ".join(
        f"{count} {operation_type}" for operation_type, count in sorted(counts_by_type.items())
    )
