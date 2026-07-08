# Architecture

## Цель архитектуры

Архитектура должна отделять пользовательский интерфейс, API, application use cases, доменные правила, инфраструктуру и будущую AI/MCP-интеграцию. Главный принцип: LLM интерпретирует запросы, но не владеет бизнес-правилами, расписанием или прямым доступом к базе.

## Monorepo

```text
gantt-mind/
├── frontend/
├── backend/
├── docs/
├── examples/
├── docker-compose.yml
├── .env.example
├── package.json
└── README.md
```

На этапе 1 реализованы только `frontend`, `backend`, базовая документация и PostgreSQL в Docker Compose.

## Backend слои

```text
backend/app/
├── api/
├── agent/
├── application/
├── domain/
├── infrastructure/
│   ├── database/
│   ├── excel/
│   └── repositories/
├── mcp/
├── config.py
└── main.py
```

На этапе 1 создан минимальный API слой для health endpoint и конфигурация.
На этапе 2 добавлен чистый `domain` слой для модели расписания и scheduler.
На этапе 3 добавлены application service, repository contract, SQLAlchemy infrastructure repository, Alembic migrations, seed и REST API чтения плана.
На этапе 5 добавлены Excel parser/exporter как infrastructure adapters и application use cases для import/export.
MCP и agent слои будут добавляться по мере этапов, без преждевременной бизнес-логики.

## Domain scheduler

Scheduler реализован как чистая domain-функция без I/O, FastAPI, SQLAlchemy, MCP, Excel или LLM SDK.

Семантика дат:

- используются календарные дни;
- `end_date` включительная;
- задача длительностью `1` день, начавшаяся `2026-01-01`, заканчивается `2026-01-01`;
- Finish-to-Start означает, что successor starts on `predecessor.end_date + 1 day`;
- входной `Task.start_date`, если задан, трактуется как explicit earliest start и не двигается назад автоматически.

Порядок расчёта определяется топологической сортировкой. Независимые задачи упорядочиваются детерминированно по `position`, затем по `id`.

## Frontend слои

```text
frontend/src/
├── app/
├── features/
├── entities/
├── shared/
└── api/
```

На этапе 1 создан `app` shell.
На этапе 4 добавлен feature-сегмент `features/plans` для read-only отображения demo-плана и Gantt chart.
Этап 4 прошёл независимую проверку и считается completed.

Текущий frontend flow:

```text
GET /api/plans/demo
→ plans API client
→ TanStack Query
→ PlanPage
→ TaskTable + GanttWorkspace
→ TaskDetailsDrawer
```

Server state хранится в TanStack Query: plan snapshot, tasks, dependencies, loading/error/retry state.
UI state остаётся локальным: выбранный `selectedTaskId`, hover task, drawer open/close и vertical row scroll synchronization.

Frontend не пересчитывает расписание и не проверяет dependency graph. Он выполняет только presentation calculations:

- timeline range;
- day columns;
- Gantt bar offset;
- Gantt bar width;
- SVG dependency coordinates;
- formatted labels.

Date-only значения API обрабатываются без `new Date("YYYY-MM-DD")`: frontend вручную парсит `YYYY-MM-DD` и считает календарные дни через UTC, чтобы избежать timezone shift.

Gantt workspace scroll model:

- left task table и right timeline являются отдельными scroll containers;
- `scrollLeft` не синхронизируется между левой и правой частями;
- header task table находится внутри левого scroll container и прокручивается горизонтально только с task table;
- timeline header находится внутри правого scroll container и прокручивается горизонтально только с timeline;
- vertical row movement остаётся синхронизированным через `scrollTop`;
- scroll synchronization не должна создавать рекурсивный scroll loop.

Dependency rendering:

- SVG dependency layer находится внутри timeline content и использует ту же систему координат, что и Gantt bars;
- horizontal scroll task table не влияет на dependency lines;
- Finish-to-Start линии начинаются в центре правого края predecessor bar и заканчиваются у центра левого края successor bar;
- dependency lines используют мягкие SVG paths с коротким финальным горизонтальным сегментом перед arrowhead;
- arrowheads остаются заметными и не должны накладываться на task bars.

## Поток будущего AI-изменения

```text
React chat
→ FastAPI endpoint
→ Agent service
→ LLM tool selection
→ MCP client
→ MCP tool
→ Application service
→ Domain validation and scheduling
→ Repository
→ PostgreSQL
→ Updated plan snapshot
```

## Архитектурные правила

- FastAPI endpoints остаются тонкими.
- React не содержит бизнес-правил расписания.
- Repository не содержит доменную логику.
- MCP tools вызывают application services.
- Scheduler детерминированный и не зависит от LLM.
- Transport DTO, domain entities и ORM models не смешиваются.

## Persistence

Этап 3 использует synchronous SQLAlchemy 2.x и PostgreSQL driver `psycopg`.

Поток чтения плана:

```text
HTTP request
→ FastAPI endpoint
→ application service
→ repository contract
→ SQLAlchemy repository
→ PostgreSQL
→ domain entities
→ Pydantic response DTO
```

Модели разделены:

- domain entities: `app.domain.entities`;
- ORM models: `app.infrastructure.database.models`;
- API DTO: `app.api.dto`.

Таблицы:

- `plans`;
- `tasks`;
- `task_dependencies`.

Удаление `Plan` каскадно удаляет связанные `Task`. Удаление `Task` каскадно удаляет связанные `TaskDependency`, где задача является predecessor или successor. Это предотвращает dangling dependencies и сохраняет целостность snapshot.

Production startup не вызывает `metadata.create_all()`. Схема создаётся через Alembic migrations. `metadata.create_all()` используется только в тестах с SQLite для быстрой проверки repository/API поведения без Docker.

## Excel import/export

Excel является external adapter и не входит в domain layer.

Import flow:

```text
Excel file
→ FastAPI multipart endpoint
→ Excel parser infrastructure adapter
→ normalized import rows
→ application import service
→ domain Plan/Task/TaskDependency
→ domain scheduler
→ repository
→ PostgreSQL
→ Plan snapshot response
```

Export flow:

```text
HTTP request
→ application/read service
→ repository
→ domain snapshot
→ Excel exporter infrastructure adapter
→ .xlsx response
```

Rules:

- Excel import contract and validation errors live in application layer.
- `openpyxl` is used only in infrastructure Excel adapters.
- `python-multipart` is used only at the FastAPI boundary.
- Domain scheduler remains the only component that calculates dates and validates dependency graph rules.
- Frontend uploads/downloads files but does not parse Excel and does not calculate schedule dates.
- Import is atomic: a plan is committed only after workbook validation, domain scheduling and repository save succeed.
- Application services depend on repository contracts and domain logic; they do not import SQLAlchemy repositories, database sessions or concrete Excel infrastructure implementations.
- API/adapters compose concrete infrastructure dependencies and call the Excel exporter for `.xlsx` responses.

## MCP adapter

Stage 6 adds a real MCP adapter layer without introducing LLM provider logic.

MCP flow:

```text
MCP client / Inspector
-> app.mcp.server tool registration
-> app.mcp.tools input validation and error mapping
-> app.mcp.runtime protocol
-> application service
-> domain operations / scheduler and repository contracts
-> infrastructure repositories
-> PostgreSQL
```

Rules:

- MCP tools are adapter functions. They validate structured input, call runtime/application services and return structured output.
- MCP tools do not import SQLAlchemy, create database sessions, execute SQL or calculate schedule dates.
- `find_tasks` is an application use case implemented by `TaskSearchService`; infrastructure runtime only composes the concrete repository and calls the service.
- `validate_plan` is an application use case implemented by `PlanValidationService`; it loads the plan through the repository contract, calls domain scheduler/validation and returns a structured validation result.
- `apply_change_set` is orchestrated by `ChangeSetService` in the application layer.
- Business rules remain in domain operations and scheduler.
- SQLAlchemy session composition lives in `app.infrastructure.mcp.runtime`.
- `change_sets` records applied MCP changes, but Undo and previous-state restore remain Stage 9 scope.
- Public MCP `apply_change_set.operations` schema uses explicit discriminated Pydantic operation models with `Literal` operation types and forbidden extra fields; it is not exposed as free-form `Mapping[str, object]`.

Stage 6 MCP surface:

- resource `ganttmind://plans/demo`;
- tool `get_plan_snapshot`;
- tool `find_tasks`;
- tool `validate_plan`;
- tool `apply_change_set`.

Stage 6 deliberately excludes LLM provider SDKs, agent prompts, frontend chat, natural-language parsing, WebSocket, auth and Undo.

## Решения этапа 1

- Root `package.json` управляет frontend workspace и общими командами.
- Backend использует `pyproject.toml`, FastAPI, pytest, ruff и mypy.
- Docker Compose на этапе 1 содержит PostgreSQL как инфраструктурную зависимость для будущего persistence.
- Health endpoint не проверяет БД, чтобы не создавать преждевременную связь до этапа persistence.

## Решения этапа 2

- Domain entities реализованы как frozen dataclasses.
- Scheduler возвращает новый `Plan` и не мутирует входное состояние.
- Поддерживается только `finish_to_start`.
- Массовые domain operations работают через временное состояние и пересчёт scheduler.

## Решения этапа 3

- Выбран synchronous SQLAlchemy, чтобы сохранить простой sync FastAPI/application поток.
- Выбран `psycopg` 3 с binary extra как современный PostgreSQL driver для SQLAlchemy 2.
- Repository contract находится в application layer и не зависит от SQLAlchemy.
- SQLAlchemy repository и mapper-функции находятся в infrastructure layer.
- API использует snake_case JSON поля.
- Demo seed отделён от HTTP endpoint и идемпотентно проверяет существование demo-плана.

## Решения этапа 4

- Выбран TanStack Query для хранения server state frontend без копирования query data в лишний local state.
- Frontend API client использует `VITE_API_BASE_URL` и typed DTO для чтения demo-плана.
- Gantt chart остаётся read-only: task selection и drawer не создают изменений в backend.
- Date-only values обрабатываются вручную через UTC calendar-day math, чтобы избежать timezone shift.
- Frontend не дублирует backend scheduler; он только отображает даты, полученные из API.
- Левая task table и правая timeline имеют независимый horizontal scroll; синхронизируется только vertical row scroll.
- Dependency SVG layer размещён в timeline coordinate system, поэтому dependency lines двигаются только вместе с правой timeline.
- Dependency arrows используют плавные SVG paths и заметные arrowheads.
- Excel, MCP, LLM, AI chat, редактирование и ChangeSet оставлены для следующих этапов.

## Решения этапа 5

- Выбран `openpyxl`, потому что он читает и пишет `.xlsx` напрямую без DataFrame-слоя.
- `pandas` не добавлен: для текущего контракта нужны строгие row-level validation errors и минимальные зависимости.
- `python-multipart` добавлен для FastAPI multipart form handling.
- Import parser отклоняет formulas и не вычисляет их.
- Predecessors используют `;` как canonical separator, чтобы не конфликтовать с запятыми в названиях задач.
- Frontend использует TanStack Query mutation; успешный import кладёт созданный plan в query cache и отображает его без full page reload.
- Routing не добавлен: для одного imported-plan перехода достаточно active query key без отдельной routing системы.
- После Verify Stage direction of dependencies уточнён: Excel import contract/errors перенесены в application layer, а exporter вызывается из API adapter.
- Excel, MCP, LLM, AI chat, ChangeSet, drag-and-drop editing and manual task editing остаются разделёнными по этапам.

## Stage 6 decisions

- The official Python MCP SDK is used for the server entry point and tool/resource registration.
- MCP input/output schemas are Pydantic models in the adapter layer; they are separate from REST DTO and domain entities.
- `apply_change_set` supports a safe MVP set of structured operations: `shift_tasks`, `change_duration`, `change_assignee`, `add_dependency`, `remove_dependency` and `delete_task`.
- Application services own orchestration and version checks; MCP tools only map inputs and errors.
- `change_sets` persists applied changes for audit/continuity, while Undo behavior is deferred to Stage 9.
