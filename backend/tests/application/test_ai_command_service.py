import json
from collections.abc import Mapping

import pytest

from app.application.ai_command_service import AiCommandService
from app.application.change_set_service import ChangeSetService
from app.application.exceptions import InvalidAiOutputError, PlanNotFoundError
from app.domain.entities import Plan
from app.infrastructure.repositories.sqlalchemy_change_set_repository import (
    SQLAlchemyChangeSetRepository,
)
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository


class FakeLLMClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_call: dict[str, object] | None = None

    def propose_operations(self, *, plan_context: Mapping[str, object], message: str) -> str:
        self.last_call = {"plan_context": dict(plan_context), "message": message}
        return self.response


def _build_service(db_session, response: str) -> AiCommandService:
    plan_repository = SQLAlchemyPlanRepository(db_session)
    change_set_repository = SQLAlchemyChangeSetRepository(db_session)
    change_set_service = ChangeSetService(plan_repository, change_set_repository)
    llm_client = FakeLLMClient(response)
    return AiCommandService(plan_repository, change_set_service, llm_client)


def test_run_command_applies_valid_operations(db_session, sample_plan: Plan) -> None:
    plan_repository = SQLAlchemyPlanRepository(db_session)
    plan_repository.save(sample_plan)
    db_session.commit()

    response = json.dumps(
        {
            "change_summary": "Task 2 now starts after task 1.",
            "operations": [
                {
                    "type": "add_dependency",
                    "predecessor_task_id": "task-1",
                    "successor_task_id": "task-2",
                }
            ],
        }
    )
    service = _build_service(db_session, response)

    result = service.run_command(plan_id="plan-1", message="Move task 2 after task 1")
    db_session.commit()

    assert result.applied is True
    assert result.change_summary == "Task 2 now starts after task 1."
    assert result.plan.version == sample_plan.version + 1


def test_run_command_with_no_operations_does_not_apply_change_set(
    db_session, sample_plan: Plan
) -> None:
    plan_repository = SQLAlchemyPlanRepository(db_session)
    plan_repository.save(sample_plan)
    db_session.commit()

    response = json.dumps({"change_summary": "This request is ambiguous.", "operations": []})
    service = _build_service(db_session, response)

    result = service.run_command(plan_id="plan-1", message="Do something vague")

    assert result.applied is False
    assert result.plan.version == sample_plan.version


def test_run_command_rejects_invalid_json(db_session, sample_plan: Plan) -> None:
    plan_repository = SQLAlchemyPlanRepository(db_session)
    plan_repository.save(sample_plan)
    db_session.commit()

    service = _build_service(db_session, "not json")

    with pytest.raises(InvalidAiOutputError):
        service.run_command(plan_id="plan-1", message="Move task 2 after task 1")


def test_run_command_rejects_unknown_task_id(db_session, sample_plan: Plan) -> None:
    plan_repository = SQLAlchemyPlanRepository(db_session)
    plan_repository.save(sample_plan)
    db_session.commit()

    response = json.dumps(
        {
            "change_summary": "Moving a task.",
            "operations": [
                {
                    "type": "change_duration",
                    "task_id": "unknown-task",
                    "duration_days": 4,
                }
            ],
        }
    )
    service = _build_service(db_session, response)

    with pytest.raises(InvalidAiOutputError):
        service.run_command(plan_id="plan-1", message="Extend the unknown task")


def test_run_command_raises_for_unknown_plan(db_session) -> None:
    service = _build_service(db_session, "{}")

    with pytest.raises(PlanNotFoundError):
        service.run_command(plan_id="missing", message="Do something")
