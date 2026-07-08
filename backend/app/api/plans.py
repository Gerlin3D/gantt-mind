from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dto import (
    ExcelValidationErrorResponse,
    PlanResponse,
    excel_validation_error_to_response,
    plan_to_response,
)
from app.application.excel_errors import ExcelValidationError, issue
from app.application.excel_service import ExcelPlanService
from app.application.exceptions import PlanNotFoundError
from app.application.plan_repository import PlanRepository
from app.application.plan_service import PlanService
from app.config import Settings, get_settings
from app.infrastructure.database.session import get_session
from app.infrastructure.excel.exporter import (
    XLSX_CONTENT_TYPE,
    export_filename,
    export_plan_to_xlsx,
)
from app.infrastructure.excel.parser import parse_import_workbook, validate_xlsx_upload
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository
from app.seed import build_demo_plan

router = APIRouter(prefix="/plans", tags=["plans"])


def get_plan_repository(session: Annotated[Session, Depends(get_session)]) -> PlanRepository:
    return SQLAlchemyPlanRepository(session)


def get_plan_service(
    repository: Annotated[PlanRepository, Depends(get_plan_repository)],
) -> PlanService:
    return PlanService(repository)


def get_excel_plan_service(
    repository: Annotated[PlanRepository, Depends(get_plan_repository)],
) -> ExcelPlanService:
    return ExcelPlanService(repository)


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


@router.get("/import/sample")
def get_import_sample_workbook() -> Response:
    sample_plan = build_demo_plan()
    return Response(
        content=export_plan_to_xlsx(sample_plan),
        media_type=XLSX_CONTENT_TYPE,
        headers={"Content-Disposition": 'attachment; filename="gantt-mind-sample.xlsx"'},
    )


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
    response_model=PlanResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ExcelValidationErrorResponse},
            status.HTTP_413_CONTENT_TOO_LARGE: {"model": ExcelValidationErrorResponse},
    },
)
async def import_plan(
    file: Annotated[UploadFile, File()],
    plan_name: Annotated[str, Form()],
    start_date: Annotated[str, Form()],
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PlanResponse | JSONResponse:
    repository = SQLAlchemyPlanRepository(session)
    service = ExcelPlanService(repository)
    content = await file.read()

    try:
        validate_xlsx_upload(
            filename=file.filename or "",
            content_type=file.content_type,
            content=content,
            max_size_bytes=settings.max_excel_upload_bytes,
        )
        rows = parse_import_workbook(content)
        plan = service.import_plan(
            plan_name=plan_name,
            start_date=_parse_start_date(start_date),
            rows=rows,
        )
        session.commit()
        return plan_to_response(plan)
    except ExcelValidationError as error:
        session.rollback()
        status_code = (
            status.HTTP_413_CONTENT_TOO_LARGE
            if any(issue.code == "file_too_large" for issue in error.issues)
            else status.HTTP_400_BAD_REQUEST
        )
        return JSONResponse(
            status_code=status_code,
            content=excel_validation_error_to_response(str(error), error.issues).model_dump(),
        )
    except Exception:
        session.rollback()
        raise


@router.get("/{plan_id}/export")
def export_plan(
    plan_id: str,
    plan_service: Annotated[PlanService, Depends(get_plan_service)],
) -> Response:
    try:
        plan = plan_service.get_plan(plan_id)
    except PlanNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan was not found: {plan_id}",
        ) from error

    return Response(
        content=export_plan_to_xlsx(plan),
        media_type=XLSX_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{export_filename(plan)}"'},
    )


def _parse_start_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ExcelValidationError(
            [
                issue(
                    "invalid_start_date",
                    "Start date must use YYYY-MM-DD format.",
                )
            ]
        ) from error
