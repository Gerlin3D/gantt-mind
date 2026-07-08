from dataclasses import dataclass

IMPORT_WORKSHEET_NAME = "Tasks"
IMPORT_COLUMNS = ("task", "description", "assignee", "duration", "predecessors")
REQUIRED_IMPORT_COLUMNS = ("task", "duration")
OPTIONAL_IMPORT_COLUMNS = ("description", "assignee", "predecessors")

EXPORT_COLUMNS = (
    "id",
    "task",
    "description",
    "assignee",
    "duration",
    "predecessors",
    "start_date",
    "end_date",
)

PREDECESSOR_SEPARATOR = ";"
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
XLSX_EXTENSION = ".xlsx"


@dataclass(frozen=True, slots=True)
class ParsedTaskRow:
    row_number: int
    task: str
    description: str
    assignee: str | None
    duration_days: int
    predecessor_names: tuple[str, ...]


def normalize_header(value: object) -> str:
    return str(value).strip().lower() if value is not None else ""


def normalize_task_name(value: str) -> str:
    return value.strip().casefold()
