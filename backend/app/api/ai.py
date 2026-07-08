from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.dto import PlanResponse, plan_to_response
from app.api.plans import get_plan_repository
from app.application.ai_command_service import AiCommandService
from app.application.change_set_repository import ChangeSetRepository
from app.application.change_set_service import ChangeSetService
from app.application.exceptions import (
    InvalidAiOutputError,
    InvalidChangeSetError,
    LlmProviderError,
    PlanNotFoundError,
    PlanVersionConflictError,
)
from app.application.llm_client import LLMClient
from app.application.plan_repository import PlanRepository
from app.config import Settings, get_settings
from app.domain.exceptions import DomainError
from app.infrastructure.database.session import get_session
from app.infrastructure.llm.openrouter_client import OpenRouterLLMClient
from app.infrastructure.repositories.sqlalchemy_change_set_repository import (
    SQLAlchemyChangeSetRepository,
)

router = APIRouter(prefix="/plans", tags=["ai"])


class AiCommandRequest(BaseModel):
    message: str = Field(min_length=1)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be blank")
        return stripped


class AiCommandResponse(BaseModel):
    plan: PlanResponse
    change_summary: str
    operations: list[dict[str, Any]]


def get_change_set_repository(
    session: Annotated[Session, Depends(get_session)],
) -> ChangeSetRepository:
    return SQLAlchemyChangeSetRepository(session)


def get_llm_client(settings: Annotated[Settings, Depends(get_settings)]) -> LLMClient:
    return OpenRouterLLMClient(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        site_url=settings.openrouter_site_url,
        app_name=settings.openrouter_app_name,
    )


def get_ai_command_service(
    plan_repository: Annotated[PlanRepository, Depends(get_plan_repository)],
    change_set_repository: Annotated[ChangeSetRepository, Depends(get_change_set_repository)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> AiCommandService:
    change_set_service = ChangeSetService(plan_repository, change_set_repository)
    return AiCommandService(plan_repository, change_set_service, llm_client)


@router.post("/{plan_id}/ai/command", response_model=AiCommandResponse)
def run_ai_command(
    plan_id: str,
    request: AiCommandRequest,
    service: Annotated[AiCommandService, Depends(get_ai_command_service)],
    session: Annotated[Session, Depends(get_session)],
) -> AiCommandResponse:
    try:
        result = service.run_command(plan_id=plan_id, message=request.message)
        session.commit()
    except PlanNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan was not found: {plan_id}",
        ) from error
    except LlmProviderError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except InvalidAiOutputError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except PlanVersionConflictError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except InvalidChangeSetError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except DomainError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return AiCommandResponse(
        plan=plan_to_response(result.plan),
        change_summary=result.change_summary,
        operations=[operation.model_dump() for operation in result.operations],
    )
