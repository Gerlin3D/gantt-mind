from datetime import date
from typing import cast

import pytest

from app.domain.entities import DependencyType, Plan, Task, TaskDependency
from app.domain.exceptions import (
    CyclicDependencyError,
    InvalidTaskDurationError,
    SelfDependencyError,
    UnknownTaskDependencyError,
    UnsupportedDependencyTypeError,
)
from app.domain.scheduler import schedule_plan, topological_sort_task_ids

PLAN_START = date(2026, 1, 1)


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
        start_date=PLAN_START,
        tasks=tasks,
        dependencies=dependencies,
    )


def task_dates(plan: Plan) -> dict[str, tuple[date | None, date | None]]:
    return {task.id: (task.start_date, task.end_date) for task in plan.tasks}


def test_schedules_one_task_without_dependencies() -> None:
    scheduled = schedule_plan(make_plan((make_task("a", duration_days=2),)))

    assert task_dates(scheduled) == {"a": (date(2026, 1, 1), date(2026, 1, 2))}


def test_schedules_multiple_independent_tasks_from_plan_start() -> None:
    scheduled = schedule_plan(make_plan((make_task("b", position=2), make_task("a", position=1))))

    assert topological_sort_task_ids(scheduled) == ("a", "b")
    assert task_dates(scheduled) == {
        "a": (date(2026, 1, 1), date(2026, 1, 1)),
        "b": (date(2026, 1, 1), date(2026, 1, 1)),
    }


def test_schedules_sequential_chain() -> None:
    scheduled = schedule_plan(
        make_plan(
            (make_task("a", duration_days=2), make_task("b", duration_days=3)),
            (TaskDependency("a", "b"),),
        )
    )

    assert task_dates(scheduled) == {
        "a": (date(2026, 1, 1), date(2026, 1, 2)),
        "b": (date(2026, 1, 3), date(2026, 1, 5)),
    }


def test_schedules_task_with_multiple_predecessors_after_latest_finish() -> None:
    scheduled = schedule_plan(
        make_plan(
            (
                make_task("a", duration_days=2, position=1),
                make_task("b", duration_days=4, position=2),
                make_task("c", duration_days=1, position=3),
            ),
            (TaskDependency("a", "c"), TaskDependency("b", "c")),
        )
    )

    assert task_dates(scheduled)["c"] == (date(2026, 1, 5), date(2026, 1, 5))


def test_schedules_branching_graph() -> None:
    scheduled = schedule_plan(
        make_plan(
            (
                make_task("a", duration_days=1, position=1),
                make_task("b", duration_days=2, position=2),
                make_task("c", duration_days=3, position=3),
            ),
            (TaskDependency("a", "b"), TaskDependency("a", "c")),
        )
    )

    assert task_dates(scheduled) == {
        "a": (date(2026, 1, 1), date(2026, 1, 1)),
        "b": (date(2026, 1, 2), date(2026, 1, 3)),
        "c": (date(2026, 1, 2), date(2026, 1, 4)),
    }


def test_preserves_later_explicit_dependent_start_date() -> None:
    delayed_task = Task(
        id="b",
        plan_id="plan-1",
        name="Task b",
        duration_days=1,
        start_date=date(2026, 1, 10),
    )
    scheduled = schedule_plan(
        make_plan((make_task("a", duration_days=1), delayed_task), (TaskDependency("a", "b"),))
    )

    assert task_dates(scheduled)["b"] == (date(2026, 1, 10), date(2026, 1, 10))


def test_rejects_self_dependency() -> None:
    with pytest.raises(SelfDependencyError):
        schedule_plan(make_plan((make_task("a"),), (TaskDependency("a", "a"),)))


def test_rejects_unknown_predecessor() -> None:
    with pytest.raises(UnknownTaskDependencyError):
        schedule_plan(make_plan((make_task("a"),), (TaskDependency("missing", "a"),)))


def test_rejects_unsupported_dependency_type() -> None:
    with pytest.raises(UnsupportedDependencyTypeError):
        schedule_plan(
            make_plan(
                (make_task("a"), make_task("b")),
                (TaskDependency("a", "b", dependency_type=cast(DependencyType, "start_to_start")),),
            )
        )


def test_rejects_simple_cycle() -> None:
    with pytest.raises(CyclicDependencyError):
        schedule_plan(
            make_plan(
                (make_task("a"), make_task("b")),
                (TaskDependency("a", "b"), TaskDependency("b", "a")),
            )
        )


def test_rejects_long_cycle() -> None:
    with pytest.raises(CyclicDependencyError):
        schedule_plan(
            make_plan(
                (make_task("a"), make_task("b"), make_task("c")),
                (
                    TaskDependency("a", "b"),
                    TaskDependency("b", "c"),
                    TaskDependency("c", "a"),
                ),
            )
        )


@pytest.mark.parametrize("duration_days", [0, -1])
def test_rejects_non_positive_duration(duration_days: int) -> None:
    with pytest.raises(InvalidTaskDurationError):
        schedule_plan(make_plan((make_task("a", duration_days=duration_days),)))


def test_topological_order_is_deterministic_for_independent_tasks() -> None:
    plan = make_plan(
        (
            make_task("c", position=2),
            make_task("b", position=1),
            make_task("a", position=1),
        )
    )

    assert topological_sort_task_ids(plan) == ("a", "b", "c")
