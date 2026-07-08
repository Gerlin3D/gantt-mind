from typing import Protocol

from app.domain.entities import Plan


class PlanRepository(Protocol):
    def save(self, plan: Plan) -> Plan:
        """Persist a new plan snapshot and return the saved domain plan."""

    def replace(self, plan: Plan) -> Plan:
        """Replace an existing plan snapshot and return the saved domain plan."""

    def get_by_id(self, plan_id: str) -> Plan | None:
        """Return a complete plan snapshot by id."""

    def get_snapshot(self, plan_id: str) -> Plan | None:
        """Return a complete plan snapshot by id."""

    def exists(self, plan_id: str) -> bool:
        """Return whether a plan exists."""
