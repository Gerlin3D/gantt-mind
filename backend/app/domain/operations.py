from dataclasses import replace
from datetime import timedelta

from app.domain.entities import Plan, Task
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
