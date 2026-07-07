from datetime import datetime
from typing import cast

from app.domain.entities import DependencyType, Plan, Task, TaskDependency
from app.infrastructure.database.models import PlanModel, TaskDependencyModel, TaskModel


def task_model_to_domain(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        plan_id=model.plan_id,
        name=model.name,
        description=model.description,
        assignee=model.assignee,
        duration_days=model.duration_days,
        start_date=model.start_date,
        end_date=model.end_date,
        position=model.position,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def dependency_model_to_domain(model: TaskDependencyModel) -> TaskDependency:
    return TaskDependency(
        predecessor_task_id=model.predecessor_task_id,
        successor_task_id=model.successor_task_id,
        dependency_type=cast(DependencyType, model.dependency_type),
    )


def plan_model_to_domain(
    model: PlanModel,
    dependencies: tuple[TaskDependencyModel, ...],
) -> Plan:
    return Plan(
        id=model.id,
        name=model.name,
        start_date=model.start_date,
        version=model.version,
        tasks=tuple(task_model_to_domain(task) for task in model.tasks),
        dependencies=tuple(dependency_model_to_domain(dependency) for dependency in dependencies),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def task_domain_to_model(task: Task) -> TaskModel:
    return TaskModel(
        id=task.id,
        plan_id=task.plan_id,
        name=task.name,
        description=task.description,
        assignee=task.assignee,
        duration_days=task.duration_days,
        start_date=task.start_date,
        end_date=task.end_date,
        position=task.position,
        created_at=cast(datetime, task.created_at) if task.created_at is not None else None,
        updated_at=cast(datetime, task.updated_at) if task.updated_at is not None else None,
    )


def dependency_domain_to_model(dependency: TaskDependency) -> TaskDependencyModel:
    return TaskDependencyModel(
        predecessor_task_id=dependency.predecessor_task_id,
        successor_task_id=dependency.successor_task_id,
        dependency_type=dependency.dependency_type,
    )


def plan_domain_to_model(plan: Plan) -> PlanModel:
    model = PlanModel(
        id=plan.id,
        name=plan.name,
        start_date=plan.start_date,
        version=plan.version,
        created_at=cast(datetime, plan.created_at) if plan.created_at is not None else None,
        updated_at=cast(datetime, plan.updated_at) if plan.updated_at is not None else None,
    )
    model.tasks = [task_domain_to_model(task) for task in plan.tasks]
    return model
