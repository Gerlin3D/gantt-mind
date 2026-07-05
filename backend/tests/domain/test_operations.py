from datetime import date

import pytest

from app.domain.entities import Plan, Task, TaskDependency
from app.domain.exceptions import InvalidTaskDurationError, UnknownTaskDependencyError
from app.domain.operations import change_task_duration, shift_tasks
from app.domain.scheduler import schedule_plan


def make_task(task_id: str, duration_days: int = 1, position: int = 0) -> Task:
    return Task(
        id=task_id,
        plan_id="plan-1",
        name=f"Task {task_id}",
        duration_days=duration_days,
        position=position,
    )


def make_plan(
    tasks: tuple[Task, ...],
    dependencies: tuple[TaskDependency, ...] = (),
) -> Plan:
    return Plan(
        id="plan-1",
        name="Demo plan",
        start_date=date(2026, 1, 1),
        tasks=tasks,
        dependencies=dependencies,
    )


def task_dates(plan: Plan) -> dict[str, tuple[date | None, date | None]]:
    return {task.id: (task.start_date, task.end_date) for task in plan.tasks}


def test_moving_predecessor_forward_moves_dependent_task_forward() -> None:
    plan = make_plan(
        (make_task("a", position=1), make_task("b", position=2)),
        (TaskDependency("a", "b"),),
    )

    shifted = shift_tasks(plan, ("a",), offset_days=3)

    assert task_dates(shifted) == {
        "a": (date(2026, 1, 4), date(2026, 1, 4)),
        "b": (date(2026, 1, 5), date(2026, 1, 5)),
    }


def test_changing_duration_reschedules_dependents() -> None:
    plan = make_plan(
        (make_task("a", position=1), make_task("b", position=2)),
        (TaskDependency("a", "b"),),
    )

    changed = change_task_duration(plan, "a", duration_days=4)

    assert task_dates(changed) == {
        "a": (date(2026, 1, 1), date(2026, 1, 4)),
        "b": (date(2026, 1, 5), date(2026, 1, 5)),
    }


def test_failed_duration_change_does_not_mutate_input_state() -> None:
    plan = make_plan((make_task("a"),))
    original_plan = plan

    with pytest.raises(InvalidTaskDurationError):
        change_task_duration(plan, "a", duration_days=0)

    assert plan == original_plan
    assert plan.tasks[0].duration_days == 1
    assert plan.tasks[0].start_date is None
    assert plan.tasks[0].end_date is None


def test_failed_shift_unknown_task_does_not_mutate_input_state() -> None:
    plan = schedule_plan(make_plan((make_task("a"),)))
    original_plan = plan

    with pytest.raises(UnknownTaskDependencyError):
        shift_tasks(plan, ("missing",), offset_days=1)

    assert plan == original_plan
