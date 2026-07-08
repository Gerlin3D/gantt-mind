from dataclasses import dataclass

from app.application.exceptions import PlanNotFoundError
from app.application.plan_repository import PlanRepository
from app.domain.entities import Plan, Task
from app.domain.exceptions import DomainError
from app.domain.scheduler import schedule_plan


@dataclass(frozen=True)
class PlanValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class PlanValidationResult:
    valid: bool
    plan: Plan | None
    errors: tuple[PlanValidationIssue, ...] = ()


class TaskSearchService:
    def __init__(self, repository: PlanRepository) -> None:
        self._repository = repository

    def find_tasks(
        self,
        *,
        plan_id: str,
        query: str | None,
        assignee: str | None,
        limit: int,
    ) -> tuple[Task, ...]:
        plan = self._get_plan(plan_id)
        normalized_query = query.casefold().strip() if query else None
        normalized_assignee = assignee.casefold().strip() if assignee else None
        matches: list[Task] = []

        for task in plan.tasks:
            if normalized_query and normalized_query not in _searchable_task_text(task):
                continue
            if normalized_assignee and (task.assignee or "").casefold() != normalized_assignee:
                continue
            matches.append(task)
            if len(matches) >= limit:
                break

        return tuple(matches)

    def _get_plan(self, plan_id: str) -> Plan:
        plan = self._repository.get_snapshot(plan_id)
        if plan is None:
            raise PlanNotFoundError(plan_id)
        return plan


class PlanValidationService:
    def __init__(self, repository: PlanRepository) -> None:
        self._repository = repository

    def validate_plan(self, plan_id: str) -> PlanValidationResult:
        plan = self._get_plan(plan_id)
        try:
            scheduled_plan = schedule_plan(plan)
        except DomainError as error:
            return PlanValidationResult(
                valid=False,
                plan=None,
                errors=(
                    PlanValidationIssue(
                        code=error.__class__.__name__,
                        message=str(error),
                    ),
                ),
            )
        return PlanValidationResult(valid=True, plan=scheduled_plan)

    def _get_plan(self, plan_id: str) -> Plan:
        plan = self._repository.get_snapshot(plan_id)
        if plan is None:
            raise PlanNotFoundError(plan_id)
        return plan


def _searchable_task_text(task: Task) -> str:
    return " ".join([task.name, task.description, task.assignee or ""]).casefold()
