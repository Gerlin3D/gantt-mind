from dataclasses import replace
from datetime import date
from typing import cast

import pytest

from app.application.change_set_service import (
    ChangeDurationChange,
    ChangeSetService,
    ShiftTasksChange,
)
from app.application.exceptions import PlanVersionConflictError
from app.domain.entities import ChangeSet, Plan
from app.domain.exceptions import InvalidTaskDurationError


class InMemoryPlanRepository:
    def __init__(self, plan: Plan) -> None:
        self.plan = plan
        self.replace_calls = 0

    def save(self, plan: Plan) -> Plan:
        self.plan = plan
        return plan

    def replace(self, plan: Plan) -> Plan:
        self.replace_calls += 1
        self.plan = plan
        return plan

    def get_by_id(self, plan_id: str) -> Plan | None:
        return self.get_snapshot(plan_id)

    def get_snapshot(self, plan_id: str) -> Plan | None:
        if self.plan.id != plan_id:
            return None
        return self.plan

    def exists(self, plan_id: str) -> bool:
        return self.plan.id == plan_id


class InMemoryChangeSetRepository:
    def __init__(self) -> None:
        self.saved: list[ChangeSet] = []

    def save(self, change_set: ChangeSet) -> ChangeSet:
        self.saved.append(change_set)
        return change_set


def test_apply_change_set_shifts_tasks_and_records_change_set(sample_plan: Plan) -> None:
    plan_repository = InMemoryPlanRepository(sample_plan)
    change_set_repository = InMemoryChangeSetRepository()
    service = ChangeSetService(plan_repository, change_set_repository)

    result = service.apply_change_set(
        plan_id=sample_plan.id,
        expected_version=sample_plan.version,
        operations=(
            ShiftTasksChange(type="shift_tasks", task_ids=("task-1",), offset_days=2),
        ),
    )

    assert result.plan.version == 2
    assert result.plan.tasks[0].start_date is not None
    assert result.plan.tasks[0].start_date > cast(date, sample_plan.tasks[0].start_date)
    assert change_set_repository.saved[0].plan_id == sample_plan.id
    assert change_set_repository.saved[0].operations[0]["type"] == "shift_tasks"


def test_apply_change_set_rejects_version_conflict_without_mutation(sample_plan: Plan) -> None:
    plan_repository = InMemoryPlanRepository(sample_plan)
    change_set_repository = InMemoryChangeSetRepository()
    service = ChangeSetService(plan_repository, change_set_repository)

    with pytest.raises(PlanVersionConflictError):
        service.apply_change_set(
            plan_id=sample_plan.id,
            expected_version=sample_plan.version + 1,
            operations=(
                ShiftTasksChange(type="shift_tasks", task_ids=("task-1",), offset_days=2),
            ),
        )

    assert plan_repository.plan == sample_plan
    assert plan_repository.replace_calls == 0
    assert change_set_repository.saved == []


def test_apply_change_set_rejects_domain_error_without_mutation(sample_plan: Plan) -> None:
    original = replace(sample_plan)
    plan_repository = InMemoryPlanRepository(sample_plan)
    change_set_repository = InMemoryChangeSetRepository()
    service = ChangeSetService(plan_repository, change_set_repository)

    with pytest.raises(InvalidTaskDurationError):
        service.apply_change_set(
            plan_id=sample_plan.id,
            expected_version=sample_plan.version,
            operations=(
                ChangeDurationChange(
                    type="change_duration",
                    task_id="task-1",
                    duration_days=0,
                ),
            ),
        )

    assert plan_repository.plan == original
    assert plan_repository.replace_calls == 0
    assert change_set_repository.saved == []
