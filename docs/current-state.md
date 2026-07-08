# Current state

## Реализовано

- Monorepo с root npm scripts и frontend workspace.
- Frontend на React + TypeScript + Vite.
- Backend на FastAPI.
- PostgreSQL через Docker Compose.
- Базовая конфигурация окружения в `.env.example`.
- `GET /api/health`.
- Доменная модель расписания: `Plan`, `Task`, `TaskDependency`.
- Deterministic scheduler с топологической сортировкой и календарными днями.
- Domain operations для переноса задач и изменения длительности.
- SQLAlchemy ORM models для `Plan`, `Task`, `TaskDependency`.
- Alembic configuration и migration `0001_create_plan_tables`.
- Repository contract, SQLAlchemy repository и ORM/domain mappers.
- Application service для чтения demo-плана и плана по ID.
- `GET /api/plans/demo` и `GET /api/plans/{plan_id}`.
- Идемпотентный demo seed.
- Frontend API configuration через `VITE_API_BASE_URL`.
- Typed frontend API client для `getDemoPlan()` и `getPlanById(planId)`.
- TanStack Query `QueryClientProvider`, query keys и hooks `useDemoPlan()` / `usePlan(planId)`.
- Read-only Gantt frontend для demo-плана:
  - project header и summary;
  - task table в порядке `position`;
  - timeline range на основе task dates;
  - Gantt bars;
  - SVG dependency layer в системе координат timeline;
  - dependency lines с плавными SVG paths и заметными arrowheads;
  - независимая горизонтальная прокрутка task table и timeline;
  - синхронизация только вертикального движения строк между table и timeline;
  - read-only task details drawer;
  - loading, error и empty states.
- Date-only frontend utilities без опасного timezone shift от `new Date("YYYY-MM-DD")`.
- Frontend tests для API client, date utilities, PlanPage states, task rendering, Gantt bar calculations, dependency rendering и drawer interaction.
- Excel import/export:
  - `POST /api/plans/import`;
  - `GET /api/plans/{plan_id}/export`;
  - `GET /api/plans/import/sample`;
  - `.xlsx` parser and exporter based on `openpyxl`;
  - structured validation report;
  - file size limit `5 MB`;
  - sample workbook `examples/gantt-mind-sample.xlsx`;
  - frontend import modal and export button;
  - import/export and round-trip tests.
- MCP adapter layer:
  - Python MCP SDK dependency;
  - `npm run backend:mcp` command;
  - MCP resource `ganttmind://plans/demo`;
  - MCP tools `get_plan_snapshot`, `find_tasks`, `validate_plan` and `apply_change_set`;
  - strict Pydantic input schemas with explicit `apply_change_set` operation models;
  - stable structured result/error contract;
  - application-level `TaskSearchService` and `PlanValidationService` for MCP query/validation use cases;
  - application-level ChangeSet service;
  - ChangeSet persistence table and repository;
  - atomic plan snapshot replacement for `apply_change_set`;
  - tests for application service, repository replacement and MCP tool behavior.

## Частично реализовано

- Docker Compose покрывает PostgreSQL, но не контейнеризует frontend/backend.

## Не реализовано

- LLM agent.
- Chat frontend.
- Undo.
- Редактирование задач и сохранение изменений из UI.
- REST endpoints for manual task editing.

## Известные ограничения

- Health endpoint не проверяет подключение к PostgreSQL.
- `docs/` находится в `.gitignore` по текущему решению владельца проекта.
- Scheduler использует календарные дни и включительный `end_date`.
- Scheduler поддерживает только Finish-to-Start зависимости.
- Backend tests выводят некритический `StarletteDeprecationWarning` про deprecated `httpx` usage в FastAPI/Starlette `TestClient`.
- Repository/API tests используют SQLite in-memory для скорости; PostgreSQL-specific поведение проверяется через реальные migration/seed команды.
- В текущей среде локальный PostgreSQL compose используется через host-порт `55432`; `.env.example` остаётся воспроизводимым с default `5432`.
- Stage 4 frontend не реализует редактирование, drag-and-drop, resize bars, optimistic updates, Excel, MCP, LLM, AI chat или ChangeSet.
- Автоматическая browser-console проверка этапа 4 не выполнена: в текущей среде не найдены Playwright/browser commands; UI behavior проверен через Vitest/jsdom tests.
- Stage 5 реализует только `.xlsx` import/export; CSV, Google Sheets и Excel Gantt rendering не поддерживаются.
- Excel import отклоняет formulas, неизвестных predecessors, self-dependencies, duplicate tasks, invalid durations и malformed workbooks.
- Excel import использует ограничение размера `MAX_EXCEL_UPLOAD_BYTES=5242880`.
- Stage 5 прошёл независимую проверку через `$verify-stage` и считается completed.
- Browser-console automation остаётся некритичным ограничением проверки: `playwright`, `chrome` и `msedge` не найдены в текущем shell-окружении.
- Stage 6 implements MCP tools but not LLM provider logic, chat UI, natural-language parsing, WebSocket, auth or Undo.
- Stage 6 `apply_change_set` supports a safe MVP operation set: `shift_tasks`, `change_duration`, `change_assignee`, `add_dependency`, `remove_dependency` and `delete_task`. `add_task` and broad `update_task` remain outside this stage.
- Stage 6 Verify blockers were fixed after the initial `FAIL`: MCP validation/search use cases now go through application services, and `apply_change_set.operations` is no longer published as a free `additionalProperties: true` object schema.
- Stage 6 passed repeat independent `$verify-stage` with `PASS WITH ISSUES`; remaining issues are non-blocking environment/tooling notes.

## Принятые решения

- Root `package.json` использует npm workspaces для frontend.
- Backend управляется через `uv` и Python 3.12.
- PostgreSQL запускается через Docker Compose.
- Domain entities являются frozen dataclasses.
- Scheduler является чистой domain-функцией без I/O и внешних SDK.
- Persistence использует synchronous SQLAlchemy 2.x и PostgreSQL driver `psycopg` 3.
- API response DTO используют snake_case поля.
- Production schema управляется через Alembic, не через `metadata.create_all()`.
- Frontend получает server state через TanStack Query.
- Frontend API base URL задаётся через `VITE_API_BASE_URL`; production URL не hardcoded.
- Frontend выполняет только presentation calculations: coordinates, widths, timeline columns и labels.
- Date-only значения парсятся вручную и считаются через UTC calendar-day math.
- Frontend не дублирует backend scheduler и не проверяет dependency graph.
- Task table и Gantt timeline имеют независимый `scrollLeft`; между левой и правой частями синхронизируется только `scrollTop`.
- Header task table прокручивается горизонтально только вместе с левой task table.
- Timeline header прокручивается горизонтально только вместе с правой timeline.
- SVG dependency layer находится внутри timeline content и движется только вместе с правой частью.
- Dependency arrows используют мягкие SVG paths с коротким финальным горизонтальным сегментом и заметными arrowheads.
- Excel parser/exporter являются infrastructure adapters и не входят в domain layer.
- Excel import создаёт новый plan через application service, domain scheduler и repository; frontend не рассчитывает даты и не проверяет dependency graph.
- Excel validation report использует row/column/code/message issues.
- `openpyxl` выбран для прямой работы с `.xlsx`; `pandas` не добавлен.
- `python-multipart` используется только на FastAPI boundary.
- Excel import contract и validation errors находятся в application layer, чтобы application service не зависел от infrastructure Excel adapters.
- Direction of dependencies checked after Verify Stage: application layer не импортирует SQLAlchemy repository, database session или concrete infrastructure implementations.
- MCP tools call application services through a runtime protocol. SQLAlchemy session/repository composition lives in infrastructure, not inside tool functions.
- MCP tools do not own business use cases: `find_tasks` delegates to `TaskSearchService`, `validate_plan` delegates to `PlanValidationService`, and `apply_change_set` delegates to `ChangeSetService`.
- MCP tools do not call the domain scheduler directly and do not query SQLAlchemy directly.

## Следующий этап

Этап 4 прошёл независимую проверку через `$verify-stage` и считается completed.
Этап 5 прошёл независимую проверку через `$verify-stage` и считается completed.

Следующий development stage определяется по `docs/development-roadmap.md`: Stage 7 LLM agent.

## Как запустить и проверить текущую версию

1. Установить frontend dependencies:

   ```bash
   npm install
   ```

2. Установить backend dependencies:

   ```bash
   cd backend
   uv python install 3.12
   uv sync --dev --python 3.12
   ```

3. Запустить PostgreSQL:

   ```bash
   docker compose up -d postgres
   ```

   Если локальный порт `5432` занят, в PowerShell можно временно переопределить порт:

   ```powershell
   $env:POSTGRES_PORT='55432'
   docker compose up -d postgres
   ```

4. Применить миграции и seed:

   ```bash
   npm run backend:migrate
   npm run backend:seed
   ```

5. Запустить long-running MCP server, если нужна MCP-проверка:

   ```bash
   npm run backend:mcp
   ```

6. Запустить backend:

   ```bash
   npm run dev:backend
   ```

7. Запустить frontend:

   ```bash
   npm run dev:frontend
   ```

8. Открыть `http://localhost:5173`.

9. Проверить команды:

   ```bash
   npm run frontend:lint
   npm run frontend:typecheck
   npm run frontend:test
   npm run frontend:build
   npm run lint
   npm run typecheck
   npm run test
   npm run build
   npm run backend:lint
   npm run backend:typecheck
   npm run backend:test
   ```

## Фактически выполненные проверки этапа 4

- `npm.cmd install @tanstack/react-query --workspace frontend` — первая попытка без escalation завершилась `EACCES` на registry; повтор с разрешением на сеть успешен, добавлены 2 packages, 0 vulnerabilities.
- `npm.cmd run frontend:lint` — первая попытка нашла лишний test import; после исправления успешно.
- `npm.cmd run frontend:typecheck` — первая попытка нашла отсутствующие Vite env types и несовместимую типизацию `vi.fn`; после исправления успешно.
- `npm.cmd run frontend:test` — первая попытка нашла неоднозначные Testing Library queries; после уточнения selectors успешно. После доработок dependency lines и scroll architecture повторная проверка прошла успешно: 5 files passed, 23 tests passed.
- `npm.cmd run frontend:build` — успешно, Vite build completed.
- `npm.cmd run lint` — успешно, frontend lint и backend ruff прошли.
- `npm.cmd run typecheck` — успешно, frontend typecheck и backend mypy прошли; mypy проверил 32 source files.
- `npm.cmd run test` — успешно, frontend 23 tests passed, backend 29 tests passed; остаётся некритический `StarletteDeprecationWarning`.
- `npm.cmd run build` — успешно, frontend production build completed.
- `npm.cmd run backend:lint` — успешно.
- `npm.cmd run backend:typecheck` — успешно, mypy проверил 32 source files.
- `npm.cmd run backend:test` — успешно, 29 tests passed; остаётся некритический `StarletteDeprecationWarning`.
- `docker compose ps` — успешно с escalation; PostgreSQL container healthy на `0.0.0.0:55432->5432`.
- Controlled uvicorn job с `DATABASE_URL=postgresql+psycopg://gantt_mind:gantt_mind@localhost:55432/gantt_mind` — `GET /api/health` вернул `health=ok`, `GET /api/plans/demo` вернул 9 tasks и 9 dependencies.
- Controlled frontend dev server job — `http://localhost:5173` вернул HTTP 200 и HTML с `id="root"`.

Автоматическая browser-console проверка не выполнена: в проекте нет Playwright, а локальные `msedge.exe`, `chrome.exe` и `playwright` commands недоступны в текущей среде. UI behavior проверен через Vitest/jsdom tests.

## Независимая проверка этапа 4

- `$verify-stage` выполнен после реализации этапа 4 и последующих исправлений dependency lines / scroll architecture.
- Итог проверки: `PASS WITH ISSUES`.
- Критических проблем не найдено.
- Этап 4 считается completed.
- Некритические замечания:
  - автоматическая browser-console проверка не выполнена из-за отсутствия Playwright/browser commands в текущей среде;
  - disabled-кнопка `Excel` в header является ранним UI affordance без реализации функциональности этапа 5.

## Фактически выполненные проверки этапа 5

- `npm.cmd run backend:lint` — успешно, ruff: all checks passed.
- `npm.cmd run backend:typecheck` — успешно, mypy: no issues found in 46 source files.
- `npm.cmd run backend:test` — успешно, 58 tests passed; остаётся некритический `StarletteDeprecationWarning`.
- `npm.cmd run frontend:lint` — успешно.
- `npm.cmd run frontend:typecheck` — успешно.
- `npm.cmd run frontend:test` — успешно, 5 files passed, 30 tests passed.
- `npm.cmd run frontend:build` — успешно, Vite production build completed.
- `npm.cmd run lint` — успешно, frontend ESLint и backend ruff прошли.
- `npm.cmd run typecheck` — успешно, frontend TypeScript и backend mypy прошли.
- `npm.cmd run test` — успешно, frontend 30 tests passed, backend 58 tests passed; остаётся некритический `StarletteDeprecationWarning`.
- `npm.cmd run build` — успешно, frontend production build completed.
- `npm.cmd run backend:generate-sample` — успешно, создан `examples/gantt-mind-sample.xlsx`.
- `docker compose ps postgres` — успешно после запуска Docker Desktop; `gantt-mind-postgres` healthy, `0.0.0.0:55432->5432/tcp`.
- `$env:DATABASE_URL='postgresql+psycopg://gantt_mind:gantt_mind@localhost:55432/gantt_mind'; npm.cmd run backend:migrate` — успешно, Alembic использовал `PostgresqlImpl`.
- `$env:DATABASE_URL='postgresql+psycopg://gantt_mind:gantt_mind@localhost:55432/gantt_mind'; npm.cmd run backend:seed` — успешно, seed идемпотентен: `Demo plan already exists.`
- Real PostgreSQL API smoke through FastAPI `TestClient` with `DATABASE_URL=postgresql+psycopg://gantt_mind:gantt_mind@localhost:55432/gantt_mind` — успешно:
  - `GET /api/health` вернул `200`;
  - `GET /api/plans/demo` вернул `200`, 9 tasks и 9 dependencies;
  - `GET /api/plans/00000000-0000-0000-0000-000000000000` вернул `404`;
  - `GET /api/plans/import/sample` вернул `.xlsx`;
  - `POST /api/plans/import` создал plan с 9 tasks и 9 dependencies;
  - `GET /api/plans/{created_plan_id}/export` вернул `.xlsx`;
  - `GET /api/plans/00000000-0000-0000-0000-000000000000/export` вернул `404`.
- `where.exe playwright`, `where.exe chrome`, `where.exe msedge` — browser automation commands не найдены.

Browser-console automation остаётся некритичным ограничением проверки этапа 5.

## Фактически выполненные проверки этапа 6

- `npm.cmd run backend:lint` — успешно, ruff: all checks passed.
- `npm.cmd run backend:typecheck` — успешно, mypy: no issues found in 60 source files.
- `npm.cmd run backend:test` — успешно, 81 tests passed; остаётся некритический `StarletteDeprecationWarning`.
- `npm.cmd run lint` — успешно, frontend ESLint и backend ruff прошли.
- `npm.cmd run typecheck` — успешно, frontend TypeScript и backend mypy прошли.
- `npm.cmd run test` — успешно, frontend 30 tests passed, backend 81 tests passed; остаётся некритический `StarletteDeprecationWarning`.
- `npm.cmd run build` — успешно, frontend production build completed.
- `npm.cmd run backend:migrate` — успешно, Alembic применил `0002_create_change_sets` на PostgreSQL.
- `uv run --project backend python -c "import app.mcp.server as server; print(type(server.mcp).__name__)"` — успешно, MCP server module loads as `FastMCP`.
- `npm.cmd exec --yes @modelcontextprotocol/inspector -- --cli --transport stdio --method tools/list -- npm.cmd run backend:mcp` — успешно после повторного запуска вне sandbox; Inspector вернул tools `get_plan_snapshot`, `find_tasks`, `validate_plan`, `apply_change_set`. `apply_change_set.operations.items` использует `oneOf` и discriminator `type`, operation definitions имеют `additionalProperties: false`.
- `npm.cmd exec --yes @modelcontextprotocol/inspector -- --cli --transport stdio --method resources/list -- npm.cmd run backend:mcp` — успешно после запуска вне sandbox; Inspector вернул resource `ganttmind://plans/demo`.

Первый запуск MCP Inspector внутри sandbox завершился `EACCES` при доступе npm к registry/cache; повторный запуск вне sandbox прошёл успешно.
