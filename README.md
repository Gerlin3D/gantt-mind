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

Frontend uses `VITE_API_BASE_URL` to reach the backend API. The default local value is:

```env
VITE_API_BASE_URL=http://localhost:8000
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

Open the frontend at `http://localhost:5173`. The read-only demo plan view calls
`GET /api/plans/demo` through `VITE_API_BASE_URL`.

Health endpoint:

```bash
curl http://localhost:8000/api/health
```

Demo plan endpoint:

```bash
curl http://localhost:8000/api/plans/demo
```

Start the MCP server for local inspector/client checks:

```bash
npm run backend:mcp
```

MCP uses the same `DATABASE_URL` as the backend API. Available Stage 6 tools are
`get_plan_snapshot`, `find_tasks`, `validate_plan`, and `apply_change_set`.

## Excel Import/Export

The frontend has an Excel import dialog and an export button in the read-only
Gantt workspace.

Supported import format is `.xlsx` with a `Tasks` worksheet and these columns:

- `task` - required unique task name.
- `description` - optional.
- `assignee` - optional.
- `duration` - required positive integer calendar-day duration.
- `predecessors` - optional `;`-separated task names.

Generate the sample workbook:

```bash
npm run backend:generate-sample
```

The sample is written to `examples/gantt-mind-sample.xlsx`.

Download the sample through the API:

```bash
curl -o gantt-mind-sample.xlsx http://localhost:8000/api/plans/import/sample
```

Export a plan:

```bash
curl -OJ http://localhost:8000/api/plans/demo-plan/export
```

The default upload limit is configured by `MAX_EXCEL_UPLOAD_BYTES` and is set to
5 MB in `.env.example`.

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
npm run backend:mcp
```

Aggregate scripts are also available:

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

## Deployment preview

This is an early preview deployment split across two Vercel projects plus an
external managed Postgres database. The MCP server is not part of this
deployment; it stays local (see below).

```text
Frontend        -> Vercel project #1 (Root Directory: frontend)
Backend FastAPI -> Vercel project #2 (Root Directory: backend)
Database        -> Neon PostgreSQL (or another managed Postgres)
MCP server      -> local only, not deployed
```

### 1. Create a Neon database

Create a free Neon project and database, then copy the **pooled** connection
string (Neon dashboard -> Connection Details -> "Pooled connection"). Pooled
connections are recommended for serverless functions, which open a new
connection per cold start.

### 2. Backend Vercel project

Create a Vercel project with:

- Root Directory: `backend`
- Framework preset: Other (the project ships its own `backend/vercel.json`
  and `backend/index.py` entrypoint for `@vercel/python`)

Environment variables:

```env
DATABASE_URL=postgresql+psycopg://user:password@host/database?sslmode=require
BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
```

Use the Neon pooled connection string for `DATABASE_URL` and keep the
`postgresql+psycopg://` scheme (matches the `psycopg` 3 driver used by
SQLAlchemy in this project). `BACKEND_CORS_ORIGINS` is a comma-separated list;
keep `http://localhost:5173` in it if you still want local frontend dev to
reach the deployed backend.

Deploy the backend project through the Vercel dashboard or `vercel deploy`
from `backend/` (do not run this without confirming with the project owner
first).

### 3. Run migrations and seed against Neon

Run these explicitly from your machine after the backend project has a
reachable `DATABASE_URL`. Migrations and seed are never run automatically at
import time, at FastAPI startup, or per request.

```powershell
$env:DATABASE_URL='<remote-neon-pooled-url>'
npm.cmd run backend:migrate
npm.cmd run backend:seed
```

### 4. Verify the backend

```bash
curl https://your-backend.vercel.app/api/health
curl https://your-backend.vercel.app/api/plans/demo
```

### 5. Frontend Vercel project

Create a second Vercel project with:

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`

Environment variable:

```env
VITE_API_BASE_URL=https://your-backend.vercel.app
```

`VITE_API_BASE_URL` is a build-time variable; set it in the Vercel project
settings before deploying so the production bundle never falls back to
`localhost`.

Deploy the frontend project through the Vercel dashboard or `vercel deploy`
from `frontend/` (do not run this without confirming with the project owner
first).

### 6. Verify the deployed app

- Open the frontend Gantt page and confirm the demo plan loads.
- Import a workbook (`npm run backend:generate-sample` produces a sample
  file) and confirm the imported plan renders.
- Export a plan and confirm the downloaded `.xlsx` opens and matches the
  plan.

### MCP scope

The MCP server (`npm run backend:mcp`) is not deployed as part of this
preview. It remains a local-only process for Inspector/client checks against
the same `DATABASE_URL`.
