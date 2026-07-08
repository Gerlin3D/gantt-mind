from datetime import date
from uuid import uuid4

from app.application.excel_contract import ParsedTaskRow, normalize_task_name
from app.application.excel_errors import ExcelValidationError, issue
from app.application.plan_repository import PlanRepository
from app.domain.entities import Plan, Task, TaskDependency
from app.domain.exceptions import CyclicDependencyError, DomainError
from app.domain.scheduler import schedule_plan


class ExcelPlanService:
    def __init__(self, repository: PlanRepository) -> None:
        self._repository = repository

    def import_plan(
        self,
        *,
        plan_name: str,
        start_date: date,
        rows: tuple[ParsedTaskRow, ...],
    ) -> Plan:
        normalized_plan_name = plan_name.strip()
        if not normalized_plan_name:
            raise ExcelValidationError(
                [issue("missing_plan_name", "Plan name must be a non-empty text value.")]
            )

        plan_id = self._new_plan_id()
        task_id_by_name = {
            normalize_task_name(row.task): f"{plan_id}-task-{index}"
            for index, row in enumerate(rows, start=1)
        }
        tasks = tuple(
            Task(
                id=task_id_by_name[normalize_task_name(row.task)],
                plan_id=plan_id,
                name=row.task,
                description=row.description,
                assignee=row.assignee,
                duration_days=row.duration_days,
                position=index,
            )
            for index, row in enumerate(rows, start=1)
        )
        dependencies = tuple(
            TaskDependency(
                predecessor_task_id=task_id_by_name[normalize_task_name(predecessor_name)],
                successor_task_id=task_id_by_name[normalize_task_name(row.task)],
            )
            for row in rows
            for predecessor_name in row.predecessor_names
        )
        plan = Plan(
            id=plan_id,
            name=normalized_plan_name,
            start_date=start_date,
            tasks=tasks,
            dependencies=dependencies,
        )

        try:
            scheduled = schedule_plan(plan)
        except CyclicDependencyError as error:
            raise ExcelValidationError(
                [issue("cyclic_dependency", "Task dependencies contain a cycle.")]
            ) from error
        except DomainError as error:
            raise ExcelValidationError(
                [issue("invalid_schedule", str(error))]
            ) from error

        return self._repository.save(scheduled)

    def _new_plan_id(self) -> str:
        while True:
            plan_id = f"plan-{uuid4().hex[:12]}"
            if not self._repository.exists(plan_id):
                return plan_id
