# Excel contract

## Supported files

- Only `.xlsx` workbooks are supported.
- Maximum upload size: `5 MB` (`MAX_EXCEL_UPLOAD_BYTES=5242880`).
- `.xls`, `.xlsm`, `.csv`, archives, Google Sheets URLs and multiple-file upload are not supported.
- Formulas in used import cells are rejected; formulas are not evaluated.

## Import worksheet

The import reads worksheet `Tasks` when present, otherwise the active worksheet.

Canonical import columns:

```text
task
description
assignee
duration
predecessors
```

Required columns:

- `task`
- `duration`

Optional columns:

- `description`
- `assignee`
- `predecessors`

Header matching is case-insensitive and trims leading/trailing spaces. No broad synonym mapping is supported.

## Row rules

- `task` must be non-empty after trim.
- Task names must be unique after trim and casefold normalization.
- `duration` must be a positive integer.
- Empty `description`, `assignee` and `predecessors` are allowed.
- Predecessors are task names separated by `;`.
- Predecessor names are trimmed and matched with the same task-name normalization.
- Unknown predecessors, self-dependencies and duplicate predecessors are rejected.
- Only `finish_to_start` dependencies are created.

## Scheduling

The Excel parser does not calculate dates. Import creates domain entities and calls the existing domain scheduler. The scheduler remains the source of truth for graph validation, cycles and calculated start/end dates.

## Validation error response

```json
{
  "code": "excel_validation_failed",
  "message": "The workbook contains invalid rows.",
  "errors": [
    {
      "worksheet": "Tasks",
      "row": 4,
      "column": "duration",
      "code": "invalid_duration",
      "message": "Duration must be a positive integer."
    }
  ]
}
```

## Export columns

```text
id
task
description
assignee
duration
predecessors
start_date
end_date
```

Export rows are ordered by task `position`. Predecessors are exported by task name using `;`, so the exported workbook can be imported again.

## Verification status

- Stage 5 independent Verify Stage passed with non-blocking issues.
- `examples/gantt-mind-sample.xlsx` was parsed successfully and matches this contract.
- Import was checked against real PostgreSQL.
- Export was checked against real PostgreSQL.
- Export → import round trip was confirmed.
- Browser-console automation remains a non-critical verification limitation in the current environment.
