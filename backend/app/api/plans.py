from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dto import PlanResponse, plan_to_response
from app.application.exceptions import PlanNotFoundError
from app.application.plan_service import PlanService
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository

router = APIRouter(prefix="/plans", tags=["plans"])


def get_plan_service(session: Annotated[Session, Depends(get_session)]) -> PlanService:
    return PlanService(SQLAlchemyPlanRepository(session))


@router.get("/demo", response_model=PlanResponse)
def get_demo_plan(
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanResponse:
    try:
        return plan_to_response(service.get_demo_plan())
    except PlanNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo plan was not found. Run backend:seed first.",
        ) from error


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanResponse:
    try:
        return plan_to_response(service.get_plan(plan_id))
    except PlanNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan was not found: {plan_id}",
        ) from error
