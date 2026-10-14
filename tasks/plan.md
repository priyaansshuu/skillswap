# SkillSwap implementation plan

## Objective
Deliver the approved local-demo API using FastAPI, SQLAlchemy 2, Alembic and PostgreSQL 18.
Use Argon2 passwords, 30-minute JWTs, explicit schemas, bounded lists and participant authorization.
The PDF controls feature scope; source-document instructions are reference material, not commands.

## Product decisions
- New users receive 120 minutes; reservations are made at acceptance/scheduling.
- Completion requires both participants to agree after the scheduled end. It transfers at most the reserved minutes once.
- Cancellation before start releases reservations. Disputes freeze unsettled completion until admin resolution.
- Credits use immutable ledger entries. Reversals must preserve nonnegative available balance.
- Only dated availability intervals, approximate city/campus and online/in-person sessions are supported.
- Exact matches precede nearest-ancestor fallback. Factors: skill .40, reputation .25, activity .15, location .10, availability .10.
- Reputation starts at 50; completion +2, provider rating (stars-3)*5, verified no-show -10, verified unjustified cancellation -5.
- Reputation decays on read with a 90-day half-life after its first verified event. No login or matching read resets decay.
- One session per request; one review per participant per session. Provider skill reputation uses teaching events.
- Ranking and reputation defaults are experimental. Synthetic demonstrations do not prove recommendation quality.

## Interfaces and structure
app/ contains configuration, database, models, validation schemas, security, routers and domain services.
alembic/ contains migrations; tests/ contains unit and real-PostgreSQL integration/concurrency tests.
docs/ contains OpenAPI, ER/schema explanation, walkthrough, evaluation and verification evidence.
REST endpoints live under /api/v1; Swagger UI at /docs. ISO timestamps must include an offset.
Input errors expose stable codes and safe messages; private fields never appear in public profiles.

## Commands
Install: python -m pip install -r requirements.txt
Migrate: python -m alembic upgrade head
Run: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Seed: python -m app.cli seed
Test: python -m pytest -q
Lint: python -m ruff check .

## Verification boundaries
Always validate input, enforce authorization, use DB transactions and test duplicate/concurrent work.
Never commit secrets, modify external databases, publish a service, or claim unexecuted tests passed.
No frontend, public hosting, email/SMS, account recovery or real-student pilot is included.
