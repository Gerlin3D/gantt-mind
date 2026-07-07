# GanttMind

GanttMind is an AI-native project plan editor. The target product combines a Gantt chart, Excel import/export, and controlled AI-assisted plan changes through application and domain services.

## Stack

- Frontend: React, TypeScript, Vite, Vitest.
- Backend: Python, FastAPI, pytest.
- Database: PostgreSQL through Docker Compose.

## Requirements

- Node.js 24+ and npm 11+ for the frontend workspace.
- uv for backend Python and dependency management.
- Docker for PostgreSQL.

Install uv with the official instructions for your platform, then make sure `uv --version` works in your shell.

## Environment

Copy `.env.example` to `.env` for local overrides:

```bash
cp .env.example .env
```

On Windows PowerShell, create the file manually or run:

```powershell
Copy-Item .env.example .env
```

## Install

Frontend dependencies:

```bash
npm install
```

Backend dependencies are managed with `uv`; manual virtual environment activation is not required.

```bash
cd backend
uv python install 3.12
uv sync --dev --python 3.12
```

This creates `backend/.venv/` and installs runtime and development dependencies from the lockfile.

## Run Locally

Start PostgreSQL:

```bash
docker compose up -d postgres
```

On Windows PowerShell, if local port `5432` is already occupied, override the published
PostgreSQL port before starting Docker Compose:

```powershell
$env:POSTGRES_PORT='55432'
docker compose up -d postgres
```

Apply database migrations and seed the demo plan:

```bash
npm run backend:migrate
npm run backend:seed
```

Start backend:

```bash
npm run dev:backend
```

Or from `backend/` directly:

```bash
uv run uvicorn app.main:app --reload
```

Start frontend:

```bash
npm run dev:frontend
```

Health endpoint:

```bash
curl http://localhost:8000/api/health
```

Demo plan endpoint:

```bash
curl http://localhost:8000/api/plans/demo
```

## Checks

Frontend:

```bash
npm run frontend:lint
npm run frontend:typecheck
npm run frontend:test
npm run frontend:build
```

Backend:

```bash
npm run backend:lint
npm run backend:typecheck
npm run backend:test
npm run backend:migrate
npm run backend:seed
```

Aggregate scripts are also available:

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```
