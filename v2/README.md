# SkillSwap v2 — frontend and backend

A working FastAPI and PostgreSQL backend for the SkillSwap college DBMS project. It covers accounts, skill discovery, matching, requests, sessions, time banking, reviews, reputation, disputes and in-app notifications.

The full React frontend is in `frontend/`. Visitors browse before login; every member can teach and learn. Build with `npm ci` and `npm run build` in that folder, then use `scripts/start-demo.ps1` to run the combined app at http://127.0.0.1:8000. [Full frontend demo and two-account walkthrough](docs/FRONTEND_DEMO.md).

## Start with Docker Desktop

Use Docker Desktop with Linux containers. From this project folder:

```powershell
Copy-Item .env.example .env
```

Edit `.env`: replace `POSTGRES_PASSWORD` with a strong **URL-safe** password and `JWT_SECRET` with a random secret of at least 32 characters. Do not publish this file. If Python is installed, generate each value with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Start the database and API, then choose a password for the synthetic demo accounts:

```powershell
docker compose up --build -d
docker compose exec api python -m app.cli seed
```

Open **http://localhost:8000/docs** for the interactive API. Log in through `POST /api/v1/auth/token` using `learner@example.com`, `teacher@example.com`, or `admin@example.com` and the password supplied to the seed command. Swagger's **Authorize** button accepts the email as username. Each login lasts 30 minutes.

Stop the demo with `docker compose down`; this preserves the database volume. Do not add `-v` unless you intend to erase the demo database.

## Start with installed Python and PostgreSQL

Requirements: Python 3.12+ and PostgreSQL 18. Create databases `skillswap` and `skillswap_test`, owned by your local database user. The test database must be disposable and its name must end in `_test`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `DATABASE_URL`, `TEST_DATABASE_URL`, and `JWT_SECRET` in `.env`. Use `postgresql+psycopg://` URLs; percent-encode any special characters in a database password.

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.cli seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The API does not create tables automatically: migrations are the source of truth. `seed` creates 15 clearly synthetic accounts, 10 skills, future availability, exact/fallback sample requests, and one historical completed exchange. It preserves existing accounts/passwords and does not duplicate starter grants on repeat runs. For a clean non-demo administrator, run `python -m app.cli create-admin` instead.

## More accounts that can both teach and learn

For accounts you can fill yourself, use **blank accounts**:

```powershell
python -m app.cli seed --blank-members 20
```

With Docker: `docker compose exec api python -m app.cli seed --blank-members 20`.

These addresses are `blank01@example.com` through `blank20@example.com`. They start without offered skills, learning goals, availability, location or bio. They still use one login and wallet for both teaching and learning. Repeating the command preserves any skills or profile details you have subsequently added. [Blank account list and customization steps](docs/BLANK_ACCOUNTS.md).

Every ordinary account can publish teaching offers and learning goals using the same login, profile and wallet. "Learner" and "teacher" describe a participant's role in a particular exchange; they are not separate account types. The original `learner@example.com` and `teacher@example.com` addresses are demonstration labels, not restrictions.

Create 20 additional members with two offered skills, two learning goals and online/in-person availability each:

```powershell
python -m app.cli seed --extra-members 20
```

With Docker, use `docker compose exec api python -m app.cli seed --extra-members 20`.

The new addresses are `member01@example.com` through `member20@example.com`. Use the password supplied to the seed command, or the configured `DEMO_PASSWORD` from your local `.env`. Repeating the command reuses these accounts and preserves their passwords and credit history. To add more later, increase the target count, up to 200; reducing it does not delete accounts. [Account list](docs/DEMO_ACCOUNTS.md).

## What to demonstrate

1. Learner logs in and reads their 120-minute starter balance.
2. Learner opens a React request and generates ranked providers.
3. Learner selects a candidate; teacher accepts, creating a session and holding 60 minutes.
4. Participants start the session when its scheduled start arrives.
5. After its end, both confirm the same duration. A single credit transfer completes the exchange.
6. Learner reviews the teacher; skill-specific reputation changes.
7. Show Pandas falling back to a Python provider, and inspect score components.
8. Show the administrator's comparison of three matching models.

See [the API walkthrough](docs/WALKTHROUGH.md) for endpoint details. The automated tests use a controlled clock to exercise completion immediately; the normal API never bypasses the real schedule. The historical seeded session provides completed-exchange data for an immediate demonstration.

## Test and inspect

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/run_tests.py
.\.venv\Scripts\python.exe -m ruff check .
```

The script reads `.env`, checks the database name, migrates that dedicated database and runs the suite. Tests truncate its application tables. Without a test database, integration tests report skipped rather than falsely passing. See [verification evidence](docs/VERIFICATION.md).

## Frontend integration

- Base URL: `http://localhost:8000/api/v1`.
- Send `Authorization: Bearer <access_token>` on protected endpoints.
- Token endpoint uses form fields `username` and `password`; other writes use JSON.
- List responses contain `items`, `limit`, and `offset`; maximum page size is 100.
- API timestamps include a UTC offset. Naive timestamps are rejected.
- Errors contain `error.code`, `error.message`, `error.details`, and a request ID.
- Configure `CORS_ORIGINS` for your frontend's actual origin.
- [OpenAPI contract](docs/openapi.json) contains request and response schemas.

## Project contents

- `app/`: API routes, domain services, schemas, authentication and configuration.
- `alembic/`: versioned schema and database integrity guards.
- `tests/`: API, accounting, concurrency, security and demo tests.
- `docs/`: walkthrough, database design, evaluation and executed verification evidence.
- `tasks/`: implementation decisions and completed build checkpoints.

This version targets a local college demo. Public deployment, email/password recovery, email/SMS delivery and real-student operation require additional work. Matching weights, score updates and decay are configurable proposed models; the seeded examples are not research results.
