from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.application.excel_errors import ExcelValidationIssue
from app.domain.entities import Plan, Task, TaskDependency


class TaskDependencyResponse(BaseModel):
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: Literal["finish_to_start"]


class TaskResponse(BaseModel):
    id: str
    name: str
    description: str
    assignee: str | None
    duration_days: int
    start_date: date | None
    end_date: date | None
    position: int


class PlanResponse(BaseModel):
    model_config = ConfigDict(title="PlanSnapshot")

    id: str
    name: str
    start_date: date
    version: int
    tasks: list[TaskResponse]
    dependencies: list[TaskDependencyResponse]


class ExcelValidationIssueResponse(BaseModel):
    worksheet: str | None = None
    row: int | None = None
    column: str | None = None
    code: str
    message: str


class ExcelValidationErrorResponse(BaseModel):
    code: Literal["excel_validation_failed"] = "excel_validation_failed"
    message: str
    errors: list[ExcelValidationIssueResponse]


def task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        assignee=task.assignee,
        duration_days=task.duration_days,
        start_date=task.start_date,
        end_date=task.end_date,
        position=task.position,
    )


def dependency_to_response(dependency: TaskDependency) -> TaskDependencyResponse:
    return TaskDependencyResponse(
        predecessor_task_id=dependency.predecessor_task_id,
        successor_task_id=dependency.successor_task_id,
        dependency_type=dependency.dependency_type,
    )


def plan_to_response(plan: Plan) -> PlanResponse:
    return PlanResponse(
        id=plan.id,
        name=plan.name,
        start_date=plan.start_date,
        version=plan.version,
        tasks=[task_to_response(task) for task in plan.tasks],
        dependencies=[dependency_to_response(dependency) for dependency in plan.dependencies],
    )


def excel_issue_to_response(issue: ExcelValidationIssue) -> ExcelValidationIssueResponse:
    return ExcelValidationIssueResponse(
        worksheet=issue.worksheet,
        row=issue.row,
        column=issue.column,
        code=issue.code,
        message=issue.message,
    )


def excel_validation_error_to_response(
    message: str,
    issues: list[ExcelValidationIssue],
) -> ExcelValidationErrorResponse:
    return ExcelValidationErrorResponse(
        message=message,
        errors=[excel_issue_to_response(validation_issue) for validation_issue in issues],
    )
