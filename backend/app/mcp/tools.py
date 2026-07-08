from collections.abc import Callable, Mapping

from pydantic import ValidationError

from app.application.exceptions import (
    ApplicationError,
    InvalidChangeSetError,
    PlanNotFoundError,
    PlanVersionConflictError,
)
from app.domain.exceptions import DomainError
from app.mcp.runtime import McpToolRuntime
from app.mcp.schemas import (
    ApplyChangeSetInput,
    FindTasksInput,
    GetPlanSnapshotInput,
    McpErrorPayload,
    McpResult,
    ValidatePlanInput,
    operation_input_to_application,
    plan_to_payload,
    task_to_payload,
)


def get_plan_snapshot_tool(
    raw_input: Mapping[str, object],
    runtime: McpToolRuntime,
) -> dict[str, object]:
    return _run_tool(
        lambda: _get_plan_snapshot(raw_input, runtime),
    )


def find_tasks_tool(
    raw_input: Mapping[str, object],
    runtime: McpToolRuntime,
) -> dict[str, object]:
    return _run_tool(
        lambda: _find_tasks(raw_input, runtime),
    )


def validate_plan_tool(
    raw_input: Mapping[str, object],
    runtime: McpToolRuntime,
) -> dict[str, object]:
    return _run_tool(
        lambda: _validate_plan(raw_input, runtime),
    )


def apply_change_set_tool(
    raw_input: Mapping[str, object],
    runtime: McpToolRuntime,
) -> dict[str, object]:
    return _run_tool(
        lambda: _apply_change_set(raw_input, runtime),
    )


def _get_plan_snapshot(
    raw_input: Mapping[str, object],
    runtime: McpToolRuntime,
) -> dict[str, object]:
    tool_input = GetPlanSnapshotInput.model_validate(raw_input)
    plan = runtime.get_plan_snapshot(tool_input.plan_id)
    return {"plan": plan_to_payload(plan)}


def _find_tasks(
    raw_input: Mapping[str, object],
    runtime: McpToolRuntime,
) -> dict[str, object]:
    tool_input = FindTasksInput.model_validate(raw_input)
    tasks = runtime.find_tasks(
        plan_id=tool_input.plan_id,
        query=tool_input.query,
        assignee=tool_input.assignee,
        limit=tool_input.limit,
    )
    return {"tasks": [task_to_payload(task) for task in tasks], "total": len(tasks)}


def _validate_plan(
    raw_input: Mapping[str, object],
    runtime: McpToolRuntime,
) -> dict[str, object]:
    tool_input = ValidatePlanInput.model_validate(raw_input)
    result = runtime.validate_plan(tool_input.plan_id)
    return {
        "valid": result.valid,
        "errors": [
            {"code": issue.code, "message": issue.message} for issue in result.errors
        ],
        "plan": plan_to_payload(result.plan) if result.plan is not None else None,
    }


def _apply_change_set(
    raw_input: Mapping[str, object],
    runtime: McpToolRuntime,
) -> dict[str, object]:
    tool_input = ApplyChangeSetInput.model_validate(raw_input)
    operations = tuple(
        operation_input_to_application(operation) for operation in tool_input.operations
    )
    applied = runtime.apply_change_set(
        plan_id=tool_input.plan_id,
        expected_version=tool_input.expected_version,
        operations=operations,
        user_request=tool_input.user_request,
    )
    return {
        "change_set_id": applied.change_set.id,
        "plan": plan_to_payload(applied.plan),
        "applied_operations": [operation.type for operation in applied.applied_operations],
        "description": applied.description,
    }


def _run_tool(handler: Callable[[], dict[str, object]]) -> dict[str, object]:
    try:
        return McpResult(ok=True, data=handler()).model_dump(mode="json")
    except ValidationError as error:
        return _error("invalid_input", "Tool input is invalid.", {"errors": error.errors()})
    except PlanNotFoundError as error:
        return _error("plan_not_found", str(error), {"plan_id": error.plan_id})
    except PlanVersionConflictError as error:
        return _error(
            "version_conflict",
            str(error),
            {
                "plan_id": error.plan_id,
                "expected_version": error.expected_version,
                "actual_version": error.actual_version,
            },
        )
    except InvalidChangeSetError as error:
        return _error("invalid_change_set", str(error))
    except DomainError as error:
        return _error("domain_validation_error", str(error))
    except ApplicationError as error:
        return _error("application_error", str(error))
    except RuntimeError as error:
        return _error("repository_error", str(error))


def _error(
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return McpResult(
        ok=False,
        error=McpErrorPayload(code=code, message=message, details=details),
    ).model_dump(mode="json")
