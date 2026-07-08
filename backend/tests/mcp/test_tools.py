from pathlib import Path
from typing import cast

from app.application.change_set_service import AppliedChangeSet, ChangeOperation
from app.application.exceptions import PlanNotFoundError
from app.application.plan_query_service import PlanValidationIssue, PlanValidationResult
from app.domain.entities import ChangeSet, Plan, Task
from app.mcp.server import mcp
from app.mcp.tools import (
    apply_change_set_tool,
    find_tasks_tool,
    get_plan_snapshot_tool,
    validate_plan_tool,
)

ToolResult = dict[str, object]


class FakeRuntime:
    def __init__(self, plan: Plan) -> None:
        self.plan = plan

    def get_plan_snapshot(self, plan_id: str) -> Plan:
        if plan_id != self.plan.id:
            raise PlanNotFoundError(plan_id)
        return self.plan

    def find_tasks(
        self,
        *,
        plan_id: str,
        query: str | None,
        assignee: str | None,
        limit: int,
    ) -> tuple[Task, ...]:
        self.get_plan_snapshot(plan_id)
        return tuple(task for task in self.plan.tasks if not query or query in task.name)[:limit]

    def validate_plan(self, plan_id: str) -> PlanValidationResult:
        return PlanValidationResult(valid=True, plan=self.get_plan_snapshot(plan_id))

    def apply_change_set(
        self,
        *,
        plan_id: str,
        expected_version: int,
        operations: tuple[ChangeOperation, ...],
        user_request: str | None,
    ) -> AppliedChangeSet:
        self.get_plan_snapshot(plan_id)
        change_set = ChangeSet(
            id="changeset-1",
            plan_id=plan_id,
            source="mcp",
            operations=tuple({"type": operation.type} for operation in operations),
            user_request=user_request,
        )
        return AppliedChangeSet(
            change_set=change_set,
            plan=self.plan,
            applied_operations=operations,
            description="1 shift_tasks",
        )


class BrokenRuntime(FakeRuntime):
    def apply_change_set(
        self,
        *,
        plan_id: str,
        expected_version: int,
        operations: tuple[ChangeOperation, ...],
        user_request: str | None,
    ) -> AppliedChangeSet:
        raise RuntimeError("database is unavailable")


class InvalidPlanRuntime(FakeRuntime):
    def validate_plan(self, plan_id: str) -> PlanValidationResult:
        self.get_plan_snapshot(plan_id)
        return PlanValidationResult(
            valid=False,
            plan=None,
            errors=(
                PlanValidationIssue(
                    code="CycleDetectedError",
                    message="Dependency cycle detected.",
                ),
            ),
        )


def test_get_plan_snapshot_tool_returns_stable_structured_response(sample_plan: Plan) -> None:
    result = get_plan_snapshot_tool({"plan_id": sample_plan.id}, FakeRuntime(sample_plan))
    data = cast(ToolResult, result["data"])
    plan = cast(ToolResult, data["plan"])

    assert result["ok"] is True
    assert result["error"] is None
    assert plan["id"] == sample_plan.id
    assert set(result.keys()) == {"ok", "data", "error"}


def test_get_plan_snapshot_tool_maps_unknown_plan(sample_plan: Plan) -> None:
    result = get_plan_snapshot_tool({"plan_id": "missing"}, FakeRuntime(sample_plan))
    error = cast(ToolResult, result["error"])

    assert result["ok"] is False
    assert error["code"] == "plan_not_found"


def test_apply_change_set_tool_validates_input(sample_plan: Plan) -> None:
    result = apply_change_set_tool(
        {"plan_id": sample_plan.id, "expected_version": 1, "operations": []},
        FakeRuntime(sample_plan),
    )
    error = cast(ToolResult, result["error"])

    assert result["ok"] is False
    assert error["code"] == "invalid_input"


def test_apply_change_set_tool_rejects_extra_operation_fields(sample_plan: Plan) -> None:
    result = apply_change_set_tool(
        {
            "plan_id": sample_plan.id,
            "expected_version": 1,
            "operations": [
                {
                    "type": "shift_tasks",
                    "task_ids": ["task-1"],
                    "offset_days": 1,
                    "unexpected": "field",
                },
            ],
        },
        FakeRuntime(sample_plan),
    )
    error = cast(ToolResult, result["error"])

    assert result["ok"] is False
    assert error["code"] == "invalid_input"


def test_apply_change_set_tool_rejects_unknown_operation_type(sample_plan: Plan) -> None:
    result = apply_change_set_tool(
        {
            "plan_id": sample_plan.id,
            "expected_version": 1,
            "operations": [
                {"type": "rewrite_everything", "task_ids": ["task-1"]},
            ],
        },
        FakeRuntime(sample_plan),
    )
    error = cast(ToolResult, result["error"])

    assert result["ok"] is False
    assert error["code"] == "invalid_input"


def test_apply_change_set_tool_returns_structured_success(sample_plan: Plan) -> None:
    result = apply_change_set_tool(
        {
            "plan_id": sample_plan.id,
            "expected_version": sample_plan.version,
            "operations": [
                {"type": "shift_tasks", "task_ids": ["task-1"], "offset_days": 1},
            ],
        },
        FakeRuntime(sample_plan),
    )
    data = cast(ToolResult, result["data"])

    assert result["ok"] is True
    assert data["change_set_id"] == "changeset-1"
    assert data["applied_operations"] == ["shift_tasks"]


def test_apply_change_set_tool_maps_repository_error(sample_plan: Plan) -> None:
    result = apply_change_set_tool(
        {
            "plan_id": sample_plan.id,
            "expected_version": sample_plan.version,
            "operations": [
                {"type": "shift_tasks", "task_ids": ["task-1"], "offset_days": 1},
            ],
        },
        BrokenRuntime(sample_plan),
    )
    error = cast(ToolResult, result["error"])

    assert result["ok"] is False
    assert error["code"] == "repository_error"


def test_find_tasks_tool_returns_matches(sample_plan: Plan) -> None:
    result = find_tasks_tool(
        {"plan_id": sample_plan.id, "query": "Discovery", "limit": 10},
        FakeRuntime(sample_plan),
    )
    data = cast(ToolResult, result["data"])
    tasks = cast(list[ToolResult], data["tasks"])

    assert result["ok"] is True
    assert data["total"] == 1
    assert tasks[0]["id"] == "task-1"


def test_validate_plan_tool_returns_structured_success(sample_plan: Plan) -> None:
    result = validate_plan_tool({"plan_id": sample_plan.id}, FakeRuntime(sample_plan))
    data = cast(ToolResult, result["data"])

    assert result["ok"] is True
    assert data["valid"] is True
    assert data["errors"] == []
    assert cast(ToolResult, data["plan"])["id"] == sample_plan.id


def test_validate_plan_tool_returns_structured_domain_errors(sample_plan: Plan) -> None:
    result = validate_plan_tool({"plan_id": sample_plan.id}, InvalidPlanRuntime(sample_plan))
    data = cast(ToolResult, result["data"])
    errors = cast(list[ToolResult], data["errors"])

    assert result["ok"] is True
    assert data["valid"] is False
    assert data["plan"] is None
    assert errors[0]["code"] == "CycleDetectedError"


def test_apply_change_set_mcp_schema_is_strict_for_operations() -> None:
    tool = next(tool for tool in mcp._tool_manager.list_tools() if tool.name == "apply_change_set")
    operations_schema = cast(ToolResult, tool.parameters["properties"])["operations"]
    operation_items = cast(ToolResult, cast(ToolResult, operations_schema)["items"])
    definitions = cast(ToolResult, tool.parameters["$defs"])

    assert "oneOf" in operation_items
    assert operation_items.get("additionalProperties") is not True
    assert cast(ToolResult, operation_items["discriminator"])["propertyName"] == "type"
    for definition in definitions.values():
        assert cast(ToolResult, definition)["additionalProperties"] is False


def test_mcp_adapter_does_not_import_sqlalchemy_directly() -> None:
    mcp_files = Path("backend/app/mcp").glob("*.py")

    for path in mcp_files:
        source = path.read_text(encoding="utf-8")
        assert "sqlalchemy" not in source.lower()
        assert "SessionLocal" not in source


def test_infrastructure_mcp_runtime_delegates_use_cases_to_application_services() -> None:
    source = Path("backend/app/infrastructure/mcp/runtime.py").read_text(encoding="utf-8")

    assert "schedule_plan" not in source
    assert "_searchable_task_text" not in source
    assert "normalized_query" not in source
    assert "casefold" not in source
    assert "PlanValidationService" in source
    assert "TaskSearchService" in source
