from dataclasses import replace

import pytest

from app.application.exceptions import PlanNotFoundError
from app.application.plan_query_service import PlanValidationService, TaskSearchService
from app.domain.entities import Plan, TaskDependency


class InMemoryPlanRepository:
    def __init__(self, plan: Plan) -> None:
        self.plan = plan

    def save(self, plan: Plan) -> Plan:
        self.plan = plan
        return plan

    def replace(self, plan: Plan) -> Plan:
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


def test_find_tasks_matches_query_assignee_and_limit(sample_plan: Plan) -> None:
    service = TaskSearchService(InMemoryPlanRepository(sample_plan))

    tasks = service.find_tasks(
        plan_id=sample_plan.id,
        query="build",
        assignee="Ivan",
        limit=1,
    )

    assert len(tasks) == 1
    assert tasks[0].id == "task-2"


def test_find_tasks_returns_empty_result(sample_plan: Plan) -> None:
    service = TaskSearchService(InMemoryPlanRepository(sample_plan))

    tasks = service.find_tasks(
        plan_id=sample_plan.id,
        query="not-present",
        assignee=None,
        limit=10,
    )

    assert tasks == ()


def test_find_tasks_raises_for_unknown_plan(sample_plan: Plan) -> None:
    service = TaskSearchService(InMemoryPlanRepository(sample_plan))

    with pytest.raises(PlanNotFoundError):
        service.find_tasks(plan_id="missing", query=None, assignee=None, limit=10)


def test_validate_plan_returns_structured_success(sample_plan: Plan) -> None:
    service = PlanValidationService(InMemoryPlanRepository(sample_plan))

    result = service.validate_plan(sample_plan.id)

    assert result.valid is True
    assert result.errors == ()
    assert result.plan is not None
    assert result.plan.id == sample_plan.id


def test_validate_plan_returns_structured_domain_error(sample_plan: Plan) -> None:
    invalid_plan = replace(
        sample_plan,
        dependencies=(TaskDependency("task-1", "task-1"),),
    )
    service = PlanValidationService(InMemoryPlanRepository(invalid_plan))

    result = service.validate_plan(invalid_plan.id)

    assert result.valid is False
    assert result.plan is None
    assert len(result.errors) == 1
    assert result.errors[0].code == "SelfDependencyError"


def test_validate_plan_raises_for_unknown_plan(sample_plan: Plan) -> None:
    service = PlanValidationService(InMemoryPlanRepository(sample_plan))

    with pytest.raises(PlanNotFoundError):
        service.validate_plan("missing")
