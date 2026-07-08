import json
from collections.abc import Mapping

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.ai import get_llm_client
from app.domain.entities import Plan
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository


class FakeLLMClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def propose_operations(self, *, plan_context: Mapping[str, object], message: str) -> str:
        return self.response


def _override_llm(client: TestClient, response: str) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(response)


def test_ai_command_applies_operations(
    client: TestClient,
    db_session: Session,
    sample_plan: Plan,
) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    _override_llm(
        client,
        json.dumps(
            {
                "change_summary": "Task 2 assigned to Nina.",
                "operations": [
                    {"type": "change_assignee", "task_ids": ["task-2"], "assignee": "Nina"}
                ],
            }
        ),
    )

    response = client.post(
        "/api/plans/plan-1/ai/command",
        json={"message": "Assign task 2 to Nina"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["change_summary"] == "Task 2 assigned to Nina."
    assert payload["plan"]["version"] == sample_plan.version + 1
    updated_task = next(task for task in payload["plan"]["tasks"] if task["id"] == "task-2")
    assert updated_task["assignee"] == "Nina"


def test_ai_command_rejects_invalid_llm_output(
    client: TestClient,
    db_session: Session,
    sample_plan: Plan,
) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    _override_llm(client, "not valid json")

    response = client.post("/api/plans/plan-1/ai/command", json={"message": "Do something"})

    assert response.status_code == 422


def test_ai_command_unknown_plan_returns_404(client: TestClient) -> None:
    _override_llm(client, json.dumps({"change_summary": "n/a", "operations": []}))

    response = client.post("/api/plans/missing/ai/command", json={"message": "Do something"})

    assert response.status_code == 404


def test_ai_command_rejects_empty_message(
    client: TestClient,
    db_session: Session,
    sample_plan: Plan,
) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    _override_llm(client, json.dumps({"change_summary": "n/a", "operations": []}))

    response = client.post("/api/plans/plan-1/ai/command", json={"message": "   "})

    assert response.status_code == 422


def test_ai_command_domain_validation_error_returns_400(
    client: TestClient,
    db_session: Session,
    sample_plan: Plan,
) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    _override_llm(
        client,
        json.dumps(
            {
                "change_summary": "Invalid duration.",
                "operations": [
                    {"type": "change_duration", "task_id": "task-1", "duration_days": 0}
                ],
            }
        ),
    )

    response = client.post("/api/plans/plan-1/ai/command", json={"message": "Zero out task 1"})

    assert response.status_code == 400
