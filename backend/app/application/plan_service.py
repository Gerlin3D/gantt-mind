from app.application.exceptions import PlanNotFoundError
from app.application.plan_repository import PlanRepository
from app.domain.entities import Plan

DEMO_PLAN_ID = "demo-plan"


class PlanService:
    def __init__(self, repository: PlanRepository) -> None:
        self._repository = repository

    def get_demo_plan(self) -> Plan:
        return self.get_plan(DEMO_PLAN_ID)

    def get_plan(self, plan_id: str) -> Plan:
        plan = self._repository.get_snapshot(plan_id)
        if plan is None:
            raise PlanNotFoundError(plan_id)
        return plan
