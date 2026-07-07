from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.entities import Plan
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository
from app.seed import build_demo_plan


def test_get_demo_plan_returns_contract(client: TestClient, db_session: Session) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(build_demo_plan())
    db_session.commit()

    response = client.get("/api/plans/demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "demo-plan"
    assert payload["name"] == "GanttMind Demo Project"
    assert payload["start_date"] == "2026-01-05"
    assert payload["version"] == 1
    assert len(payload["tasks"]) == 9
    assert len(payload["dependencies"]) == 9
    assert set(payload["tasks"][0]) == {
        "id",
        "name",
        "description",
        "assignee",
        "duration_days",
        "start_date",
        "end_date",
        "position",
    }
    assert set(payload["dependencies"][0]) == {
        "predecessor_task_id",
        "successor_task_id",
        "dependency_type",
    }


def test_get_plan_by_id_returns_snapshot(
    client: TestClient,
    db_session: Session,
    sample_plan: Plan,
) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    response = client.get("/api/plans/plan-1")

    assert response.status_code == 200
    assert response.json()["id"] == "plan-1"


def test_get_missing_plan_returns_404(client: TestClient) -> None:
    response = client.get("/api/plans/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan was not found: missing"
