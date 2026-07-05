from collections import defaultdict
from dataclasses import replace
from datetime import timedelta

from app.domain.entities import Plan, Task, TaskDependency
from app.domain.exceptions import (
    CyclicDependencyError,
    DuplicateTaskIdError,
    InvalidTaskDurationError,
    SelfDependencyError,
    TaskPlanMismatchError,
    UnknownTaskDependencyError,
    UnsupportedDependencyTypeError,
)


def schedule_plan(plan: Plan) -> Plan:
    tasks_by_id = _validate_and_index_tasks(plan)
    predecessors = _validate_dependencies(plan.dependencies, tasks_by_id)
    ordered_ids = topological_sort_task_ids(plan)
    scheduled_tasks: dict[str, Task] = {}

    for task_id in ordered_ids:
        task = tasks_by_id[task_id]
        earliest_start = plan.start_date

        for predecessor_id in predecessors[task_id]:
            predecessor_end_date = scheduled_tasks[predecessor_id].end_date
            if predecessor_end_date is None:
                continue
            earliest_start = max(earliest_start, predecessor_end_date + timedelta(days=1))

        if task.start_date is not None:
            earliest_start = max(earliest_start, task.start_date)

        end_date = earliest_start + timedelta(days=task.duration_days - 1)
        scheduled_tasks[task_id] = replace(task, start_date=earliest_start, end_date=end_date)

    return replace(plan, tasks=tuple(scheduled_tasks[task_id] for task_id in ordered_ids))


def topological_sort_task_ids(plan: Plan) -> tuple[str, ...]:
    tasks_by_id = _validate_and_index_tasks(plan)
    _validate_dependencies(plan.dependencies, tasks_by_id)

    adjacency: dict[str, list[str]] = {task_id: [] for task_id in tasks_by_id}
    indegree: dict[str, int] = {task_id: 0 for task_id in tasks_by_id}

    for dependency in plan.dependencies:
        adjacency[dependency.predecessor_task_id].append(dependency.successor_task_id)
        indegree[dependency.successor_task_id] += 1

    for successors in adjacency.values():
        successors.sort(key=lambda task_id: _task_order(tasks_by_id[task_id]))

    ready = sorted(
        [task_id for task_id, degree in indegree.items() if degree == 0],
        key=lambda task_id: _task_order(tasks_by_id[task_id]),
    )
    ordered: list[str] = []

    while ready:
        task_id = ready.pop(0)
        ordered.append(task_id)

        for successor_id in adjacency[task_id]:
            indegree[successor_id] -= 1
            if indegree[successor_id] == 0:
                ready.append(successor_id)
                ready.sort(key=lambda ready_task_id: _task_order(tasks_by_id[ready_task_id]))

    if len(ordered) != len(tasks_by_id):
        raise CyclicDependencyError()

    return tuple(ordered)


def _validate_and_index_tasks(plan: Plan) -> dict[str, Task]:
    tasks_by_id: dict[str, Task] = {}

    for task in plan.tasks:
        if task.id in tasks_by_id:
            raise DuplicateTaskIdError(task.id)
        if task.plan_id != plan.id:
            raise TaskPlanMismatchError(task.id, plan.id)
        if task.duration_days <= 0:
            raise InvalidTaskDurationError(task.id, task.duration_days)
        tasks_by_id[task.id] = task

    return tasks_by_id


def _validate_dependencies(
    dependencies: tuple[TaskDependency, ...],
    tasks_by_id: dict[str, Task],
) -> dict[str, tuple[str, ...]]:
    predecessors: dict[str, list[str]] = defaultdict(list)

    for task_id in tasks_by_id:
        predecessors[task_id] = []

    for dependency in dependencies:
        if dependency.dependency_type != "finish_to_start":
            raise UnsupportedDependencyTypeError(dependency.dependency_type)
        if dependency.predecessor_task_id == dependency.successor_task_id:
            raise SelfDependencyError(dependency.predecessor_task_id)
        if dependency.predecessor_task_id not in tasks_by_id:
            raise UnknownTaskDependencyError(dependency.predecessor_task_id)
        if dependency.successor_task_id not in tasks_by_id:
            raise UnknownTaskDependencyError(dependency.successor_task_id)
        predecessors[dependency.successor_task_id].append(dependency.predecessor_task_id)

    return {
        task_id: tuple(sorted(task_predecessors, key=lambda item: _task_order(tasks_by_id[item])))
        for task_id, task_predecessors in predecessors.items()
    }


def _task_order(task: Task) -> tuple[int, str]:
    return (task.position, task.id)
