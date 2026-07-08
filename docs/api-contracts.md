# API contracts

## Current endpoints

### GET /api/health

Возвращает состояние backend-сервиса.

Response `200`:

```json
{
  "status": "ok",
  "service": "GanttMind API",
  "environment": "development"
}
```

Назначение endpoint: инфраструктурная проверка запуска backend. Он не проверяет PostgreSQL на этапе 1.

### GET /api/plans/demo

Возвращает засидированный demo-план.

Response `200`:

```json
{
  "id": "demo-plan",
  "name": "GanttMind Demo Project",
  "start_date": "2026-01-05",
  "version": 1,
  "tasks": [
    {
      "id": "discovery",
      "name": "Project discovery",
      "description": "",
      "assignee": "Maya",
      "duration_days": 2,
      "start_date": "2026-01-05",
      "end_date": "2026-01-06",
      "position": 1
    }
  ],
  "dependencies": [
    {
      "predecessor_task_id": "discovery",
      "successor_task_id": "requirements",
      "dependency_type": "finish_to_start"
    }
  ]
}
```

Response `404`: demo-план отсутствует, нужно выполнить seed.

### GET /api/plans/{plan_id}

Возвращает полный snapshot плана по ID.

Response `200`: тот же shape, что `GET /api/plans/demo`.

Response `404`:

```json
{
  "detail": "Plan was not found: missing"
}
```

### POST /api/plans/import

Imports a project plan from an `.xlsx` workbook.

Request:

```http
POST /api/plans/import
Content-Type: multipart/form-data
```

Fields:

- `file` — `.xlsx` workbook, maximum `5 MB`;
- `plan_name` — non-empty plan name;
- `start_date` — ISO date in `YYYY-MM-DD` format.

Response `201`: full plan snapshot, same shape as `GET /api/plans/{plan_id}`.

Validation response `400`:

```json
{
  "code": "excel_validation_failed",
  "message": "The workbook contains invalid rows.",
  "errors": [
    {
      "worksheet": "Tasks",
      "row": 2,
      "column": "duration",
      "code": "invalid_duration",
      "message": "Duration must be a positive integer."
    }
  ]
}
```

Response `413`: same validation error shape with `file_too_large`.

Verification status: checked on real PostgreSQL during Stage 5 Verify Stage. Successful import creates a new scheduled plan atomically; validation failures do not persist partial plans.

### GET /api/plans/import/sample

Downloads a sample `.xlsx` workbook matching the import contract.

Response `200`:

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="gantt-mind-sample.xlsx"`

Verification status: sample workbook was parsed against the Excel contract and contains 9 tasks and 9 dependencies.

### GET /api/plans/{plan_id}/export

Exports a saved plan as `.xlsx`.

Response `200`:

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="<plan-name>.xlsx"`

Response `404`:

```json
{
  "detail": "Plan was not found: missing"
}
```

Verification status: export was checked on real PostgreSQL during Stage 5 Verify Stage. Export → import round trip is covered by backend tests and API smoke.

## Planned endpoints

```text
PATCH  /api/plans/{plan_id}/tasks/{task_id}
POST   /api/plans/{plan_id}/chat
POST   /api/plans/{plan_id}/undo
```

Планируемые endpoints будут уточняться на этапах 7, 8 и 9.
