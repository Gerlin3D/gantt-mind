from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from app.application.excel_contract import EXPORT_COLUMNS
from app.domain.entities import Plan
from app.infrastructure.excel.exporter import export_filename, export_plan_to_xlsx
from app.infrastructure.excel.parser import parse_import_workbook


def test_export_plan_writes_expected_rows(sample_plan: Plan) -> None:
    workbook = load_workbook(BytesIO(export_plan_to_xlsx(sample_plan)))
    worksheet = workbook["Tasks"]

    assert [cell.value for cell in worksheet[1]] == list(EXPORT_COLUMNS)
    assert worksheet["A2"].value == "task-1"
    assert worksheet["B2"].value == "Discovery"
    assert worksheet["E2"].value == 2
    assert worksheet["G2"].value.date() == sample_plan.tasks[0].start_date
    assert worksheet["H2"].value.date() == sample_plan.tasks[0].end_date
    assert worksheet["F3"].value == "Discovery"
    assert worksheet.freeze_panes == "A2"
    assert worksheet.auto_filter.ref is not None


def test_exported_workbook_can_be_parsed_for_round_trip(sample_plan: Plan) -> None:
    rows = parse_import_workbook(export_plan_to_xlsx(sample_plan))

    assert [row.task for row in rows] == ["Discovery", "Implementation"]
    assert rows[1].predecessor_names == ("Discovery",)


def test_export_filename_is_stable() -> None:
    assert export_filename(
        Plan(id="plan-1", name="My Imported Plan", start_date=sample_plan_start_date())
    ) == "my-imported-plan.xlsx"


def sample_plan_start_date() -> date:
    return date(2026, 1, 1)
