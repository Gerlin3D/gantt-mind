from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.plans import get_plan_service
from app.application.plan_service import PlanService
from app.domain.entities import Plan, Task, TaskDependency
from app.domain.scheduler import schedule_plan
from app.infrastructure.database import models  # noqa: F401
from app.infrastructure.database.base import Base
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository
from app.main import create_app


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with session_factory() as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sample_plan() -> Plan:
    plan = Plan(
        id="plan-1",
        name="Repository test plan",
        start_date=date(2026, 2, 2),
        tasks=(
            Task(
                id="task-1",
                plan_id="plan-1",
                name="Discovery",
                description="Understand scope",
                assignee="Maya",
                duration_days=2,
                position=1,
            ),
            Task(
                id="task-2",
                plan_id="plan-1",
                name="Implementation",
                description="Build backend",
                assignee="Ivan",
                duration_days=3,
                position=2,
            ),
        ),
        dependencies=(TaskDependency("task-1", "task-2"),),
    )
    return schedule_plan(plan)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    app = create_app()

    def override_plan_service() -> PlanService:
        return PlanService(SQLAlchemyPlanRepository(db_session))

    app.dependency_overrides[get_plan_service] = override_plan_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
