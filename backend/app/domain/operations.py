from dataclasses import replace
from datetime import timedelta

from app.domain.entities import Plan, Task, TaskDependency
from app.domain.exceptions import InvalidTaskDurationError, UnknownTaskDependencyError
from app.domain.scheduler import schedule_plan


def shift_tasks(plan: Plan, task_ids: tuple[str, ...], offset_days: int) -> Plan:
    scheduled_plan = schedule_plan(plan)
    task_ids_to_shift = set(task_ids)
    scheduled_tasks_by_id = {task.id: task for task in scheduled_plan.tasks}

    for task_id in task_ids_to_shift:
        if task_id not in scheduled_tasks_by_id:
            raise UnknownTaskDependencyError(task_id)

    shifted_tasks: list[Task] = []

    for task in scheduled_plan.tasks:
        if task.id not in task_ids_to_shift:
            shifted_tasks.append(task)
            continue

        if task.start_date is None:
            raise UnknownTaskDependencyError(task.id)

        shifted_tasks.append(
            replace(
                task,
                start_date=task.start_date + timedelta(days=offset_days),
                end_date=None,
            )
        )

    return schedule_plan(replace(plan, tasks=tuple(shifted_tasks)))


def change_task_duration(plan: Plan, task_id: str, duration_days: int) -> Plan:
    if duration_days <= 0:
        raise InvalidTaskDurationError(task_id, duration_days)

    if task_id not in {task.id for task in plan.tasks}:
        raise UnknownTaskDependencyError(task_id)

    updated_tasks = tuple(
        replace(task, duration_days=duration_days, end_date=None) if task.id == task_id else task
        for task in plan.tasks
    )

    return schedule_plan(replace(plan, tasks=updated_tasks))


def change_task_assignee(
    plan: Plan,
    task_ids: tuple[str, ...],
    assignee: str | None,
) -> Plan:
    tasks_by_id = {task.id: task for task in plan.tasks}
    task_ids_to_update = set(task_ids)

    for task_id in task_ids_to_update:
        if task_id not in tasks_by_id:
            raise UnknownTaskDependencyError(task_id)

    updated_tasks = tuple(
        replace(task, assignee=assignee) if task.id in task_ids_to_update else task
        for task in plan.tasks
    )
    return replace(plan, tasks=updated_tasks)


def add_finish_to_start_dependency(
    plan: Plan,
    predecessor_task_id: str,
    successor_task_id: str,
) -> Plan:
    dependency = TaskDependency(
        predecessor_task_id=predecessor_task_id,
        successor_task_id=successor_task_id,
    )
    if dependency in plan.dependencies:
        return schedule_plan(plan)
    return schedule_plan(replace(plan, dependencies=(*plan.dependencies, dependency)))


def remove_finish_to_start_dependency(
    plan: Plan,
    predecessor_task_id: str,
    successor_task_id: str,
) -> Plan:
    updated_dependencies = tuple(
        dependency
        for dependency in plan.dependencies
        if not (
            dependency.predecessor_task_id == predecessor_task_id
            and dependency.successor_task_id == successor_task_id
        )
    )
    return schedule_plan(replace(plan, dependencies=updated_dependencies))


def delete_task(plan: Plan, task_id: str) -> Plan:
    if task_id not in {task.id for task in plan.tasks}:
        raise UnknownTaskDependencyError(task_id)

    updated_tasks = tuple(task for task in plan.tasks if task.id != task_id)
    updated_dependencies = tuple(
        dependency
        for dependency in plan.dependencies
        if dependency.predecessor_task_id != task_id and dependency.successor_task_id != task_id
    )
    return schedule_plan(replace(plan, tasks=updated_tasks, dependencies=updated_dependencies))
