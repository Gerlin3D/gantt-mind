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

### POST /api/plans/{plan_id}/ai/command

Sends a natural-language instruction to the backend, which asks an OpenRouter
model (via the OpenAI-compatible client) for a strict JSON operation proposal
and applies it through the existing ChangeSet pipeline (same domain
validation/scheduler/repository path as MCP `apply_change_set`).

Request:

```json
{
  "message": "Move QA testing after Integration"
}
```

Response `200`:

```json
{
  "plan": { "...updated plan snapshot..." },
  "change_summary": "QA testing now starts after Integration.",
  "operations": [
    {
      "type": "add_dependency",
      "predecessor_task_id": "integration",
      "successor_task_id": "qa-testing"
    }
  ]
}
```

If the instruction is ambiguous or cannot be mapped to allowed operations
using only known task ids, the response still returns `200` with
`operations: []`, an unchanged `plan`, and a clarification message in
`change_summary`. No ChangeSet is applied in that case.

Supported operation types: `shift_tasks`, `change_duration`,
`change_assignee`, `add_dependency`, `remove_dependency` — the same shapes
already used by `apply_change_set` (see MCP contracts below). `delete_task` is
intentionally not exposed to the AI command.

Error responses (`detail` message, no raw traceback):

- `404` — unknown `plan_id`.
- `422` — empty/blank `message`, or the AI provider returned output that is
  not valid JSON or does not match the expected schema (including unknown
  task ids).
- `502` — missing `OPENROUTER_API_KEY` or an AI provider request failure.
- `409` — plan version conflict (concurrent update).
- `400` — domain/ChangeSet validation error (e.g. invalid duration).

`OPENROUTER_API_KEY` must be set only on the backend; the frontend never
receives it or the model name.

## Planned endpoints

```text
PATCH  /api/plans/{plan_id}/tasks/{task_id}
POST   /api/plans/{plan_id}/undo
```

Планируемые endpoints будут уточняться на этапах 8 и 9.

## MCP contracts

Stage 6 MCP tools return a stable structured envelope:

```json
{
  "ok": true,
  "data": {},
  "error": null
}
```

Error response:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "plan_not_found",
    "message": "Plan was not found: missing",
    "details": {
      "plan_id": "missing"
    }
  }
}
```

### Resource `ganttmind://plans/demo`

Returns the same structured envelope as `get_plan_snapshot` for `demo-plan`.

### Tool `get_plan_snapshot`

Input:

```json
{
  "plan_id": "demo-plan"
}
```

Success `data` contains `plan` with the same snapshot fields as `GET /api/plans/{plan_id}`.

### Tool `find_tasks`

Input:

```json
{
  "plan_id": "demo-plan",
  "query": "API",
  "assignee": null,
  "limit": 20
}
```

Success `data` contains `tasks` and `total`.

### Tool `validate_plan`

Input:

```json
{
  "plan_id": "demo-plan"
}
```

Success `data` contains `valid`, `errors` and `plan`.

### Tool `apply_change_set`

Input:

```json
{
  "plan_id": "demo-plan",
  "expected_version": 1,
  "operations": [
    {
      "type": "shift_tasks",
      "task_ids": ["discovery"],
      "offset_days": 1
    }
  ],
  "user_request": "Move discovery one day later."
}
```

Supported Stage 6 operations:

- `shift_tasks`;
- `change_duration`;
- `change_assignee`;
- `add_dependency`;
- `remove_dependency`;
- `delete_task`.

The public MCP schema for `operations` is a discriminated union keyed by `type`.
Each operation has explicit required fields, `Literal` operation type values and
forbids extra properties. `operations.items` must not be exposed as a free-form
object with `additionalProperties: true`.

Success `data` contains `change_set_id`, updated `plan`, `applied_operations` and `description`.

Errors use these codes:

- `invalid_input`;
- `plan_not_found`;
- `version_conflict`;
- `invalid_change_set`;
- `domain_validation_error`;
- `application_error`;
- `repository_error`.
