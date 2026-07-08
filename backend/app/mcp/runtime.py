from typing import Protocol

from app.application.change_set_service import AppliedChangeSet, ChangeOperation
from app.application.plan_query_service import PlanValidationResult
from app.domain.entities import Plan, Task


class McpToolRuntime(Protocol):
    def get_plan_snapshot(self, plan_id: str) -> Plan:
        """Return a plan snapshot or raise an application error."""

    def find_tasks(
        self,
        *,
        plan_id: str,
        query: str | None,
        assignee: str | None,
        limit: int,
    ) -> tuple[Task, ...]:
        """Return matching tasks for a plan."""

    def validate_plan(self, plan_id: str) -> PlanValidationResult:
        """Validate and return a structured plan validation result."""

    def apply_change_set(
        self,
        *,
        plan_id: str,
        expected_version: int,
        operations: tuple[ChangeOperation, ...],
        user_request: str | None,
    ) -> AppliedChangeSet:
        """Apply a validated ChangeSet through application services."""
