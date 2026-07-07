import pytest
from sqlalchemy.orm import Session

from app.application.exceptions import PlanNotFoundError
from app.application.plan_service import DEMO_PLAN_ID, PlanService
from app.domain.entities import Plan
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository
from app.seed import build_demo_plan


def test_get_plan_returns_existing_plan(db_session: Session, sample_plan: Plan) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()
    service = PlanService(repository)

    plan = service.get_plan("plan-1")

    assert plan.id == "plan-1"


def test_get_demo_plan_returns_seeded_demo_plan(db_session: Session) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(build_demo_plan())
    db_session.commit()
    service = PlanService(repository)

    plan = service.get_demo_plan()

    assert plan.id == DEMO_PLAN_ID
    assert len(plan.tasks) == 9


def test_get_plan_raises_for_missing_plan(db_session: Session) -> None:
    service = PlanService(SQLAlchemyPlanRepository(db_session))

    with pytest.raises(PlanNotFoundError):
        service.get_plan("missing")
