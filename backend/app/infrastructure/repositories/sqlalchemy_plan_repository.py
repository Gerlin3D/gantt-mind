from sqlalchemy import exists, select
from sqlalchemy.orm import Session, selectinload

from app.domain.entities import Plan
from app.infrastructure.database.models import PlanModel, TaskDependencyModel, TaskModel
from app.infrastructure.repositories.mappers import (
    dependency_domain_to_model,
    plan_domain_to_model,
    plan_model_to_domain,
)


class SQLAlchemyPlanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, plan: Plan) -> Plan:
        model = plan_domain_to_model(plan)
        self._session.add(model)
        self._session.flush()

        for dependency in plan.dependencies:
            self._session.add(dependency_domain_to_model(dependency))

        self._session.flush()
        return self.get_snapshot(plan.id) or plan

    def get_by_id(self, plan_id: str) -> Plan | None:
        return self.get_snapshot(plan_id)

    def get_snapshot(self, plan_id: str) -> Plan | None:
        model = self._session.scalar(
            select(PlanModel)
            .where(PlanModel.id == plan_id)
            .options(selectinload(PlanModel.tasks))
        )
        if model is None:
            return None

        task_ids = [task.id for task in model.tasks]
        dependencies: tuple[TaskDependencyModel, ...] = ()
        if task_ids:
            dependencies = tuple(
                self._session.scalars(
                    select(TaskDependencyModel)
                    .where(
                        TaskDependencyModel.predecessor_task_id.in_(task_ids),
                        TaskDependencyModel.successor_task_id.in_(task_ids),
                    )
                    .join(
                        TaskModel,
                        TaskModel.id == TaskDependencyModel.successor_task_id,
                    )
                    .order_by(TaskModel.position, TaskDependencyModel.predecessor_task_id)
                )
            )

        return plan_model_to_domain(model, dependencies)

    def exists(self, plan_id: str) -> bool:
        return self._session.scalar(select(exists().where(PlanModel.id == plan_id))) is True
