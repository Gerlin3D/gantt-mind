from dataclasses import dataclass

from pydantic import ValidationError

from app.application.ai_contract import (
    AiOperation,
    AiOperationProposal,
    ai_operation_to_change,
    build_plan_context,
    referenced_task_ids,
)
from app.application.change_set_service import ChangeOperation, ChangeSetService
from app.application.exceptions import InvalidAiOutputError, PlanNotFoundError
from app.application.llm_client import LLMClient
from app.application.plan_repository import PlanRepository
from app.domain.entities import Plan


@dataclass(frozen=True, slots=True)
class AiCommandResult:
    plan: Plan
    change_summary: str
    operations: tuple[AiOperation, ...]
    applied: bool


class AiCommandService:
    def __init__(
        self,
        plan_repository: PlanRepository,
        change_set_service: ChangeSetService,
        llm_client: LLMClient,
    ) -> None:
        self._plan_repository = plan_repository
        self._change_set_service = change_set_service
        self._llm_client = llm_client

    def run_command(self, *, plan_id: str, message: str) -> AiCommandResult:
        plan = self._plan_repository.get_snapshot(plan_id)
        if plan is None:
            raise PlanNotFoundError(plan_id)

        plan_context = build_plan_context(plan)
        raw_output = self._llm_client.propose_operations(
            plan_context=plan_context,
            message=message,
        )

        try:
            proposal = AiOperationProposal.model_validate_json(raw_output)
        except ValidationError as error:
            raise InvalidAiOutputError(
                "The AI provider returned output that does not match the expected schema."
            ) from error
        except ValueError as error:
            raise InvalidAiOutputError(
                "The AI provider returned output that is not valid JSON."
            ) from error

        if not proposal.operations:
            return AiCommandResult(
                plan=plan,
                change_summary=proposal.change_summary,
                operations=(),
                applied=False,
            )

        known_task_ids = {task.id for task in plan.tasks}
        unknown_task_ids: set[str] = set()
        for operation in proposal.operations:
            unknown_task_ids |= referenced_task_ids(operation) - known_task_ids
        if unknown_task_ids:
            raise InvalidAiOutputError(
                "The AI provider referenced unknown task ids: "
                + ", ".join(sorted(unknown_task_ids))
            )

        change_operations: tuple[ChangeOperation, ...] = tuple(
            ai_operation_to_change(operation) for operation in proposal.operations
        )

        applied = self._change_set_service.apply_change_set(
            plan_id=plan_id,
            expected_version=plan.version,
            operations=change_operations,
            source="ai",
            user_request=message,
        )

        return AiCommandResult(
            plan=applied.plan,
            change_summary=proposal.change_summary,
            operations=tuple(proposal.operations),
            applied=True,
        )
