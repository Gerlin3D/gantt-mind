from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.excel_contract import ParsedTaskRow
from app.application.excel_errors import ExcelValidationError
from app.application.excel_service import ExcelPlanService
from app.infrastructure.database.models import PlanModel
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository


def test_import_plan_schedules_and_persists_snapshot(db_session: Session) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    service = ExcelPlanService(repository)

    plan = service.import_plan(
        plan_name="Imported Plan",
        start_date=date(2026, 3, 2),
        rows=(
            ParsedTaskRow(2, "Discovery", "Scope", "Maya", 2, ()),
            ParsedTaskRow(3, "Build", "", "Ivan", 3, ("Discovery",)),
        ),
    )
    db_session.commit()

    loaded = repository.get_snapshot(plan.id)

    assert loaded is not None
    assert loaded.name == "Imported Plan"
    assert [task.name for task in loaded.tasks] == ["Discovery", "Build"]
    assert loaded.tasks[0].start_date == date(2026, 3, 2)
    assert loaded.tasks[0].end_date == date(2026, 3, 3)
    assert loaded.tasks[1].start_date == date(2026, 3, 4)
    assert len(loaded.dependencies) == 1


def test_import_plan_rejects_cycles_without_persisting_plan(db_session: Session) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    service = ExcelPlanService(repository)

    with pytest.raises(ExcelValidationError) as error:
        service.import_plan(
            plan_name="Broken Plan",
            start_date=date(2026, 3, 2),
            rows=(
                ParsedTaskRow(2, "A", "", None, 1, ("B",)),
                ParsedTaskRow(3, "B", "", None, 1, ("A",)),
            ),
        )

    db_session.rollback()

    assert error.value.issues[0].code == "cyclic_dependency"
    assert db_session.scalar(select(func.count()).select_from(PlanModel)) == 0


def test_import_plan_requires_name(db_session: Session) -> None:
    service = ExcelPlanService(SQLAlchemyPlanRepository(db_session))

    with pytest.raises(ExcelValidationError) as error:
        service.import_plan(
            plan_name="  ",
            start_date=date(2026, 3, 2),
            rows=(ParsedTaskRow(2, "A", "", None, 1, ()),),
        )

    assert error.value.issues[0].code == "missing_plan_name"
