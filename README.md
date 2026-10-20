# SkillSwap

SkillSwap is a campus skill-exchange platform where members earn time credits by teaching and spend them to learn. Each person uses one account, profile, and wallet for both roles. The current local demonstration combines a React and TypeScript frontend, a FastAPI backend, and PostgreSQL.

## What the application supports

- Account registration, login, profiles, teaching offers, learning goals, and availability.
- Public skill discovery and provider matching by skill relevance, reputation, recent activity, location, and schedule availability. When no exact-skill providers qualify, matching can fall back through the skill hierarchy.
- Requests, scheduled sessions, confirmations, in-app notifications, reviews, disputes, and administrative actions.
- Time credits recorded as integer minutes. Accepting a session reserves credits; both participants confirm completion before one ledger transfer is settled. Reversals are linked to the original accounting event and audited.

Matching weights and reputation decay settings are configurable demonstration parameters. The repository does not report a user study establishing ranking quality or improved outcomes.

## Architecture

| Component | Role |
| --- | --- |
| `frontend/` | React, TypeScript, and Vite single-page application. |
| `v2/` | FastAPI routes and services, Pydantic validation, SQLAlchemy database access, and JWT bearer authentication. |
| PostgreSQL | Authoritative application records and integrity constraints. Alembic migrations manage schema changes. |
| In-app notifications | Stored in PostgreSQL and delivered through the API; external email and SMS delivery are outside the local demo. |

The database has 18 application tables covering accounts, skills and user-skill associations, availability, requests and matching history, sessions and reservations, credit ledger entries, reviews and reputation events, disputes, notifications, blocks, administrator audit, and authentication attempts. The accompanying [database notes](v2/docs/DATABASE.md) and [schema reference](v2/docs/schema.sql) describe the model and integrity rules.

## Run the local demo

The documented launcher uses PowerShell. A fresh setup requires Python 3.12 or later, PostgreSQL 18, Node.js 22.12 or later, and a PostgreSQL database named `skillswap`. Follow the detailed [backend setup](v2/README.md) and [frontend walkthrough](v2/docs/FRONTEND_DEMO.md) if you need Docker, database creation, or account-seeding details.

From the repository root, install and build the frontend, then prepare the backend environment:

```powershell
Set-Location frontend
npm ci
npm run build
Set-Location ../v2
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `v2/.env` with the connection details for your local PostgreSQL database and a random `JWT_SECRET` of at least 32 characters. Keep `.env` and all secret values out of Git. Create the database before running migrations. Then seed synthetic demonstration data and start the app:

```powershell
.\.venv\Scripts\python.exe -m app.cli seed --blank-members 20
.\scripts\start-demo.ps1
```

The launcher applies migrations, builds the frontend if needed, and serves the combined application at **http://127.0.0.1:8000**. The interactive API documentation is available at `/docs`; readiness is available at `/health/ready`. Stop the managed application with `v2/scripts/stop-demo.ps1`. This does not remove PostgreSQL data.

A Docker Compose setup is documented in [v2/README.md](v2/README.md) and [v2/compose.yaml](v2/compose.yaml). Docker startup was not included in the repository's recorded verification run.

## Development

Run the API from `v2/` on port 8000 and the Vite development server from `frontend/` on port 5173. Vite proxies API requests to the backend. See the [frontend demo guide](v2/docs/FRONTEND_DEMO.md) for the full local workflow and two-account walkthrough.

## Verification and evaluation

The repository's [verification record](v2/docs/VERIFICATION.md), dated 14 October 2026, reports 32 passing automated tests with no skips in a PostgreSQL run, plus API smoke, persistence, migration, and lint evidence. The checks used synthetic data. They support the documented local workflows; they do not establish recommendation quality, real-student outcomes, public deployment, or production readiness. Ranking relevance, acceptance, completion, satisfaction, response time, and repeat use are proposed measures for future evaluation.

To see the complete test scope, prerequisites, and database-safety notes, follow the test instructions in [v2/README.md](v2/README.md).

## Repository map

- `frontend/` — React and TypeScript application, API client, unit tests, and browser checks.
- `v2/app/` — FastAPI application, services, schemas, authentication, and CLI.
- `v2/alembic/` — versioned PostgreSQL migrations and integrity guards.
- `v2/tests/` — backend API, accounting, concurrency, security, and workflow tests.
- `v2/docs/` — API, database, setup, demo, evaluation, and verification documentation.

