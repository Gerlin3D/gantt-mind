from sqlalchemy.orm import Session

from app.domain.entities import Plan
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository


def test_saves_and_gets_plan_snapshot(db_session: Session, sample_plan: Plan) -> None:
    repository = SQLAlchemyPlanRepository(db_session)

    saved = repository.save(sample_plan)
    db_session.commit()
    loaded = repository.get_by_id(saved.id)

    assert loaded is not None
    assert loaded.id == sample_plan.id
    assert loaded.name == sample_plan.name
    assert [task.id for task in loaded.tasks] == ["task-1", "task-2"]
    assert loaded.tasks[0].start_date is not None
    assert loaded.tasks[1].end_date is not None
    assert loaded.dependencies == sample_plan.dependencies


def test_get_snapshot_loads_tasks_and_dependencies(db_session: Session, sample_plan: Plan) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    snapshot = repository.get_snapshot("plan-1")

    assert snapshot is not None
    assert len(snapshot.tasks) == 2
    assert len(snapshot.dependencies) == 1
    assert snapshot.dependencies[0].predecessor_task_id == "task-1"
    assert snapshot.dependencies[0].successor_task_id == "task-2"


def test_exists_returns_false_for_missing_plan(db_session: Session) -> None:
    repository = SQLAlchemyPlanRepository(db_session)

    assert repository.exists("missing") is False
    assert repository.get_by_id("missing") is None


def test_orm_domain_mapping_preserves_snapshot(db_session: Session, sample_plan: Plan) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    saved = repository.save(sample_plan)

    assert saved == repository.get_snapshot(sample_plan.id)


def test_replace_updates_existing_plan_snapshot(db_session: Session, sample_plan: Plan) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    updated = Plan(
        id=sample_plan.id,
        name="Updated plan",
        start_date=sample_plan.start_date,
        version=sample_plan.version + 1,
        tasks=(sample_plan.tasks[0],),
        dependencies=(),
    )

    saved = repository.replace(updated)
    db_session.commit()
    loaded = repository.get_snapshot(sample_plan.id)

    assert saved.name == "Updated plan"
    assert loaded is not None
    assert loaded.version == 2
    assert [task.id for task in loaded.tasks] == ["task-1"]
    assert loaded.dependencies == ()
