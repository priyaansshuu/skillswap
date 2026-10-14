# SkillSwap full local demo

The React frontend in the repository's top-level `frontend/` folder and FastAPI backend in `v2/` run together. A single account teaches and learns; public visitors browse without signing in. The built app uses initials avatars and actual database records.

## Start on this laptop

Use the workspace launcher in outputs/Start_SkillSwap_Demo.ps1. It uses the existing ignored local configuration and PostgreSQL service. If PostgreSQL is stopped, start that local database first. Open http://127.0.0.1:8000 after the launcher reports ready.

## Start from a fresh checkout

Requirements: Python 3.12+, PostgreSQL, Node.js compatible with the pinned frontend dependencies (Node 24.14 verified), and Microsoft Edge for the supplied browser tests.

1. Follow README.md to create the Python environment, local .env, and databases. Keep database credentials, JWT_SECRET, and DEMO_PASSWORD out of Git.
2. From the repository's top-level frontend/, run `npm ci` and `npm run build`.
3. From v2/, run `.\.venv\Scripts\python.exe -m alembic upgrade head`.
4. Seed the accounts you need. To preserve a chosen shared demo password, configure DEMO_PASSWORD in your ignored .env, load it into the process when running the CLI, or enter it when prompted. `python -m app.cli seed --blank-members 20` creates the customizable blank accounts; existing profiles and balances remain intact.
5. Run `.\scripts\start-demo.ps1`. If the Python environment is elsewhere, pass `-Python C:\path\to\python.exe`.
6. Open http://127.0.0.1:8000. The built frontend is served by FastAPI, including direct navigation to /profile, /credits, and other app routes.
7. Stop only the managed app with `.\scripts\stop-demo.ps1`. This does not stop PostgreSQL or remove its data.

For development, run FastAPI from v2/ on port 8000 and `npm run dev` in the top-level frontend/. Vite runs on 5173 and proxies /api to FastAPI. Optional SKILLSWAP_API_URL changes the proxy target; never put database credentials or JWT secrets into frontend environment variables.

## Two-account presentation

Use two independent browser sessions, for example Edge and a Chrome private window. Log in with blank01@example.com and blank02@example.com using your configured shared demo password. Registration also creates a fresh account with 120 starter minutes.

1. In the first account, open Teach a skill. Add a name/bio, an offered skill such as React, a learning goal, and an online availability window starting at a future minute and lasting at least ten minutes.
2. In the second account, add any offered skill and a React learning goal. This demonstrates that both accounts can teach and learn.
3. Browse React, open the first member's profile, choose two minutes and a window overlapping that availability, then check availability.
4. Review the suggested start, tick the confirmation, and send the request. Browsing and checking availability create no request records.
5. In the first account, open My activity → Requests and accept. The second account's wallet now reserves two minutes.
6. Wait for the actual scheduled start, then start the session. Completion remains disabled until the actual scheduled end; the demo does not bypass this rule.
7. After the end, have one account confirm one minute and the other confirm two. The app shows a disagreement and transfers nothing.
8. Update the second confirmation to one minute. Both sessions show completed; the learner has 119 minutes, the teacher 121, and each ledger shows one transfer, assuming both began with 120.
9. Add a review, inspect notifications, and show the updated public teaching-rating summary. Review text remains private to the session participants.
10. Suggest a missing skill, then log in as admin@example.com in another independent session. Approve it in Admin → Skill suggestions and add it to a member's skills.

A rejected request does not reserve credits. Cancelling before the start releases reservations. After the start, use Report a problem for administrator review. Every administrator resolution records an immutable audit entry.

## Verification commands

- Backend: install requirements-dev.txt and run pytest with TEST_DATABASE_URL loaded from your ignored .env; it must name a disposable database ending in _test.
- Frontend: `npm test`, `npm run build`, and `npx prettier --check src e2e *.ts`.
- Full browser acceptance: build first, then run `python scripts/run_browser_checks.py` from v2/. It creates/resets only skillswap_browser_test on your loopback PostgreSQL server, seeds synthetic accounts with a temporary password, starts an isolated API on 8001, and runs Microsoft Edge headlessly against the production build. It never resets your demo database. The real two-minute exchange makes this check take several minutes.
- For Chromium instead of Edge, change the Playwright channel after installing the corresponding browser; Edge is the verified Windows default.

The hosting, messaging, video calls, maps, and photo uploads excluded from the approved first build remain outside this demo.
