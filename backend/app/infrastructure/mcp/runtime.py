from app.application.change_set_service import AppliedChangeSet, ChangeOperation, ChangeSetService
from app.application.plan_query_service import (
    PlanValidationResult,
    PlanValidationService,
    TaskSearchService,
)
from app.application.plan_service import PlanService
from app.domain.entities import Plan, Task
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.repositories.sqlalchemy_change_set_repository import (
    SQLAlchemyChangeSetRepository,
)
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository


class SQLAlchemyMcpToolRuntime:
    def get_plan_snapshot(self, plan_id: str) -> Plan:
        with SessionLocal() as session:
            repository = SQLAlchemyPlanRepository(session)
            return PlanService(repository).get_plan(plan_id)

    def find_tasks(
        self,
        *,
        plan_id: str,
        query: str | None,
        assignee: str | None,
        limit: int,
    ) -> tuple[Task, ...]:
        with SessionLocal() as session:
            repository = SQLAlchemyPlanRepository(session)
            return TaskSearchService(repository).find_tasks(
                plan_id=plan_id,
                query=query,
                assignee=assignee,
                limit=limit,
            )

    def validate_plan(self, plan_id: str) -> PlanValidationResult:
        with SessionLocal() as session:
            repository = SQLAlchemyPlanRepository(session)
            return PlanValidationService(repository).validate_plan(plan_id)

    def apply_change_set(
        self,
        *,
        plan_id: str,
        expected_version: int,
        operations: tuple[ChangeOperation, ...],
        user_request: str | None,
    ) -> AppliedChangeSet:
        with SessionLocal() as session:
            plan_repository = SQLAlchemyPlanRepository(session)
            change_set_repository = SQLAlchemyChangeSetRepository(session)
            service = ChangeSetService(plan_repository, change_set_repository)

            try:
                result = service.apply_change_set(
                    plan_id=plan_id,
                    expected_version=expected_version,
                    operations=operations,
                    source="mcp",
                    user_request=user_request,
                )
                session.commit()
            except Exception:
                session.rollback()
                raise

            return result


def build_mcp_tool_runtime() -> SQLAlchemyMcpToolRuntime:
    return SQLAlchemyMcpToolRuntime()
