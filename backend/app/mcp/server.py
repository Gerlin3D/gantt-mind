import json

from mcp.server.fastmcp import FastMCP

from app.application.plan_service import DEMO_PLAN_ID
from app.infrastructure.mcp.runtime import build_mcp_tool_runtime
from app.mcp.schemas import ChangeOperationInput
from app.mcp.tools import (
    apply_change_set_tool,
    find_tasks_tool,
    get_plan_snapshot_tool,
    validate_plan_tool,
)

runtime = build_mcp_tool_runtime()
mcp = FastMCP(
    "GanttMind MCP",
    instructions=(
        "Structured tools for reading and safely changing GanttMind project plans. "
        "Tools call application services; schedule rules remain in the domain layer."
    ),
)


@mcp.tool(name="get_plan_snapshot")
def get_plan_snapshot(plan_id: str) -> dict[str, object]:
    return get_plan_snapshot_tool({"plan_id": plan_id}, runtime)


@mcp.tool(name="find_tasks")
def find_tasks(
    plan_id: str,
    query: str | None = None,
    assignee: str | None = None,
    limit: int = 20,
) -> dict[str, object]:
    return find_tasks_tool(
        {
            "plan_id": plan_id,
            "query": query,
            "assignee": assignee,
            "limit": limit,
        },
        runtime,
    )


@mcp.tool(name="validate_plan")
def validate_plan(plan_id: str) -> dict[str, object]:
    return validate_plan_tool({"plan_id": plan_id}, runtime)


@mcp.tool(name="apply_change_set")
def apply_change_set(
    plan_id: str,
    expected_version: int,
    operations: list[ChangeOperationInput],
    user_request: str | None = None,
) -> dict[str, object]:
    return apply_change_set_tool(
        {
            "plan_id": plan_id,
            "expected_version": expected_version,
            "operations": operations,
            "user_request": user_request,
        },
        runtime,
    )


@mcp.resource("ganttmind://plans/demo")
def demo_plan_resource() -> str:
    result = get_plan_snapshot_tool({"plan_id": DEMO_PLAN_ID}, runtime)
    return json.dumps(result, ensure_ascii=False)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
