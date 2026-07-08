from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExcelValidationIssue:
    code: str
    message: str
    worksheet: str | None = None
    row: int | None = None
    column: str | None = None


class ExcelValidationError(Exception):
    def __init__(self, issues: list[ExcelValidationIssue]) -> None:
        super().__init__("The workbook contains invalid rows.")
        self.issues = issues


def issue(
    code: str,
    message: str,
    *,
    worksheet: str | None = None,
    row: int | None = None,
    column: str | None = None,
) -> ExcelValidationIssue:
    return ExcelValidationIssue(
        code=code,
        message=message,
        worksheet=worksheet,
        row=row,
        column=column,
    )
