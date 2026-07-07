# Development roadmap

## Этап 1. Каркас проекта и документация

Статус: completed.

- Monorepo.
- React + TypeScript + Vite.
- FastAPI.
- Docker Compose.
- PostgreSQL.
- Конфигурация окружения.
- Health endpoint.
- Базовая документация.
- Команды запуска.
- Lint, typecheck, test и build команды.

Окружение backend управляется через `uv`: Python 3.12, `.venv`, dev dependencies и `uv.lock`.

## Этап 2. Доменная модель и scheduler

Статус: completed; independent Verify Stage passed with non-blocking issues.

- Plan.
- Task.
- TaskDependency.
- Доменные ошибки.
- Граф зависимостей.
- Проверка циклов.
- Топологическая сортировка.
- Расчёт дат.
- Unit-тесты.

Реализовано без persistence, SQLAlchemy, Alembic, API endpoints, Excel, MCP, LLM и frontend.

Некритический технический долг: backend tests выводят `StarletteDeprecationWarning` про deprecated `httpx` usage в FastAPI/Starlette `TestClient`.

## Этап 3. Persistence и API плана

Статус: completed; independent Verify Stage passed with non-blocking issues.

- SQLAlchemy models.
- Alembic migrations.
- Repositories.
- Application services.
- Seed data.
- Demo-plan API.
- Plan by ID API.
- Integration tests.

Проверено:

- `GET /api/plans/demo` возвращает demo-план с 9 задачами и 9 зависимостями.
- `GET /api/plans/{plan_id}` возвращает plan snapshot по ID.
- Неизвестный plan ID возвращает HTTP 404.
- Alembic upgrade, downgrade и повторный upgrade проверены на PostgreSQL.
- Demo seed проверен на идемпотентность.
- Некритический технический долг: backend tests выводят `StarletteDeprecationWarning` про deprecated `httpx` usage в FastAPI/Starlette `TestClient`.

## Этап 4. Gantt frontend

Статус: completed; independent Verify Stage passed with non-blocking issues.

- API client.
- TanStack Query.
- Gantt.
- Выбор задачи.
- Модальное окно.
- Loading, empty и error states.

Реализовано:

- Frontend API base URL через `VITE_API_BASE_URL`.
- Typed API client для `GET /api/plans/demo` и `GET /api/plans/{plan_id}`.
- TanStack Query provider, query keys и hooks.
- Read-only project header и summary.
- Task table в порядке `position`.
- Timeline на календарных днях с weekend/month/today markers.
- Gantt bars на основе backend `start_date`, `end_date` и `duration_days`.
- SVG dependency layer для Finish-to-Start связей.
- Date-only значения обрабатываются без timezone shift.
- Frontend не дублирует backend scheduler и не проверяет dependency graph.
- Левая task table и правая timeline имеют независимую горизонтальную прокрутку.
- Header task table прокручивается горизонтально только вместе с левой частью.
- Timeline header прокручивается горизонтально только вместе с правой частью.
- Вертикальное движение строк синхронизировано между task table и timeline.
- `scrollLeft` не синхронизируется между левой и правой частями.
- SVG dependency layer находится в системе координат timeline.
- Dependency lines используют плавные SVG paths и заметные arrowheads.
- Read-only details drawer.
- Loading, error и empty states.
- Frontend tests для API client, date utilities, PlanPage, Gantt и drawer behavior.

Проверено:

- `$verify-stage` выполнен после завершения этапа 4.
- Итог независимой проверки: `PASS WITH ISSUES`.
- Критических проблем не найдено.
- Frontend загружает demo-план через `GET /api/plans/demo`.
- `npm.cmd run frontend:lint`, `npm.cmd run frontend:typecheck`, `npm.cmd run frontend:test`, `npm.cmd run frontend:build`, `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run test` и `npm.cmd run build` прошли.
- Некритический технический долг: автоматическая browser-console проверка не выполнена из-за отсутствия Playwright/browser commands в текущей среде.

Не реализовано на этапе 4:

- Excel import/export.
- Редактирование задач.
- Drag-and-drop и resize bars.
- Optimistic updates.
- ChangeSet.
- MCP.
- LLM.
- AI chat.

## Этап 5. Excel import/export

- Загрузка файла.
- Validation report.
- Создание плана.
- Экспорт.
- `examples/example-plan.xlsx`.
- Round-trip tests.

## Этап 6. MCP server

- MCP configuration.
- MCP resources.
- MCP tools.
- `apply_change_set`.
- Проверка через MCP Inspector.
- Integration tests.

## Этап 7. LLM agent

- Provider interface.
- Рабочий provider.
- Tool schemas.
- Agent system prompt.
- Tool calls.
- Mock provider для тестов.
- Ограничение количества итераций.

## Этап 8. Chat frontend

- Chat panel.
- Отправка сообщения.
- Состояние выполнения.
- Ответ агента.
- Список применённых изменений.
- Обновление Gantt.
- Обработка ошибок.

## Этап 9. Undo и полировка

- Сохранение previous state.
- Отмена последнего ChangeSet.
- UX-улучшения.
- Дополнительные тесты.

## Этап 10. Подготовка сдачи

- README.
- Архитектура.
- Принятые решения.
- AI-assisted development.
- Roadmap to production.
- Demo GIF или видео.
- Deployment.
- Проверка полного сценария.
