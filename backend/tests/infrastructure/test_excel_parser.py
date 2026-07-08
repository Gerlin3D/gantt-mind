import pytest

from app.application.excel_errors import ExcelValidationError
from app.infrastructure.excel.parser import parse_import_workbook, validate_xlsx_upload
from tests.infrastructure.excel_workbook_helpers import workbook_bytes


def test_parse_valid_workbook_with_multiple_predecessors() -> None:
    content = workbook_bytes(
        [
            ["Task", "Description", "Assignee", "Duration", "Predecessors"],
            ["Discovery", "Scope", "Maya", 2, ""],
            ["Build", "", "Ivan", 3, "Discovery"],
            ["QA", "", "", 1, "Discovery;Build"],
        ]
    )

    rows = parse_import_workbook(content)

    assert [row.task for row in rows] == ["Discovery", "Build", "QA"]
    assert rows[2].predecessor_names == ("Discovery", "Build")
    assert rows[2].assignee is None


def test_parse_headers_case_insensitive_and_trimmed() -> None:
    content = workbook_bytes(
        [
            [" TASK ", " duration "],
            ["Discovery", "2"],
        ]
    )

    rows = parse_import_workbook(content)

    assert rows[0].task == "Discovery"
    assert rows[0].duration_days == 2


@pytest.mark.parametrize(
    ("rows", "code"),
    [
        ([["task"], ["Discovery"]], "missing_required_column"),
        ([["task", "duration"], ["", 1]], "missing_task"),
        ([["task", "duration"], ["Discovery", 0]], "invalid_duration"),
        ([["task", "duration"], ["Discovery", -1]], "invalid_duration"),
        ([["task", "duration"], ["Discovery", 1.5]], "invalid_duration"),
        ([["task", "duration"], ["Discovery", "soon"]], "invalid_duration"),
        ([["task", "duration"], ["Discovery", 1], [" discovery ", 2]], "duplicate_task"),
        ([["task", "duration", "predecessors"], ["Build", 1, "Missing"]], "unknown_predecessor"),
        ([["task", "duration", "predecessors"], ["Build", 1, "Build"]], "self_dependency"),
        (
            [
                ["task", "duration", "predecessors"],
                ["Build", 1, "Discovery;Discovery"],
                ["Discovery", 1, ""],
            ],
            "duplicate_predecessor",
        ),
        ([["task", "duration"], ["Discovery", "=1+1"]], "formula_not_allowed"),
    ],
)
def test_parse_validation_errors(rows: list[list[object]], code: str) -> None:
    with pytest.raises(ExcelValidationError) as error:
        parse_import_workbook(workbook_bytes(rows))

    assert any(issue.code == code for issue in error.value.issues)


def test_parse_empty_workbook_fails() -> None:
    with pytest.raises(ExcelValidationError) as error:
        parse_import_workbook(workbook_bytes([]))

    assert error.value.issues[0].code == "empty_workbook"


def test_parse_malformed_workbook_fails() -> None:
    with pytest.raises(ExcelValidationError) as error:
        parse_import_workbook(b"not an xlsx")

    assert error.value.issues[0].code == "malformed_workbook"


def test_validate_upload_rejects_extension_content_type_and_size() -> None:
    with pytest.raises(ExcelValidationError) as error:
        validate_xlsx_upload(
            filename="plan.csv",
            content_type="text/csv",
            content=b"123456",
            max_size_bytes=3,
        )

    assert {issue.code for issue in error.value.issues} == {
        "unsupported_file_type",
        "unsupported_content_type",
        "file_too_large",
    }
