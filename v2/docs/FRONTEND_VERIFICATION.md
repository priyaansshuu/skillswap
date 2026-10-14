# SkillSwap frontend verification

Executed on Windows on 14 October 2026 against local PostgreSQL, Python 3.12+, Node.js 24.14 and Microsoft Edge. This record covers the approved React frontend and its compatible backend additions.

## Executed checks

| Check | Result | Scope |
| --- | --- | --- |
| PostgreSQL backend suite | 40 passed | Existing regression suite and public privacy, blocked users, preview without persistence, credits/availability revalidation, concurrent idempotency, teaching ratings, suggestions, administrator access and ownership tests |
| Frontend interaction suite | 6 passed in 3 files | Shared field accessibility, API/error handling and provider-card selection/forwarding |
| TypeScript and production build | Passed | Strict types including generated OpenAPI schemas; Vite production bundle |
| Ruff and Prettier | Passed | Backend lint and frontend source/test formatting |
| Shipping dependency audit | No known vulnerabilities reported | `npm audit --omit=dev` at verification time |
| Browser acceptance | Passed across full and focused runs | Eight distinct scenarios described below; production frontend served by FastAPI against isolated PostgreSQL |
| Windows launcher | Start, stop and restart passed | Combined app at http://127.0.0.1:8000 with existing local configuration; the laptop launcher starts its native database on the configured 55432 port |

The browser results are accumulated full and focused runs, not a claim that every scenario ran in one final invocation. Test-only locator corrections were followed by focused reruns. The read-only mode-state regression also passed against the combined demo on port 8000. No recorded test password, token or local `.env` is part of the source package.

## Browser scenarios

1. Anonymous discovery loads actual catalog/member records and routes to public profiles.
2. Two independent browser contexts use the same account capabilities for teaching and learning. They add skills and availability, preview and submit a two-minute exchange, accept with reservation, wait for the **real scheduled start and end**, disagree on duration, then match on one minute. The learner finishes with 119 minutes, teacher with 121, and exactly one transfer is recorded. A review is submitted. The browser run does not bypass the clock.
3. A member suggests a skill, an administrator approves it, the member adds it, and member access to administrator routes is denied. Audit/evaluation, logout and client expiry are checked.
4. Registration creates a blank account with 120 minutes and labelled, usable fields.
5. A member opens a dispute on an independent **seeded historical completed exchange**; the administrator dismisses it. The record remains completed with its one existing transfer. This test checks dispute handling, not a newly conducted second exchange.
6. In-person discovery forwards the chosen mode through the profile and login return path to an eligible booking preview.
7. Desktop (1469px), phone (390px), tablet (768px), the 817px reference panel and results (1505px) are checked for overflow and browser errors. Mobile filters and navigation work.
8. Changing the mode in the results sidebar, browser history or mobile drawer updates the top search control. Clearing filters selects Any mode; resubmitting does not silently restore an old mode. Homepage search retains the intended Online default.

`scripts/run_browser_checks.py` creates/resets only the loopback database `skillswap_browser_test`, migrates it, creates synthetic fixtures with a temporary password, and serves the built frontend on port 8001. The demo database is preserved. Run it after `npm run build`; see [demo instructions](FRONTEND_DEMO.md).

## Data and UI evidence

The demo migration reached `003_frontend`; its existing **55 accounts** were preserved, including blank01–blank20. Public responses exclude email, learning goals, wallets and private review text. Rating stars summarize teaching reviews; reputation remains separately labelled. Existing exchange APIs remain compatible.

Approved mockups and runtime captures are retained under `.impeccable/mocks/` and `.impeccable/review/`. The independent finish reviewer inspected all three approved comps and eleven runtime captures. Its material mode-state finding was corrected and verified; its documentation follow-up is this file. Representative token contrast calculations exceed 4.5:1, and forms, focus states, skip navigation, native dialogs and reduced-motion behavior are present. These checks do not constitute a complete accessibility certification.

## Delivery limits

This is an executed local laptop demo. Docker startup was not rerun for this frontend release; native Windows Python/PostgreSQL startup was verified. Public deployment, production load, real student usage, password recovery, messaging, calls, maps and photo storage were not part of this build. Generated mockup sample members are replaced by actual API data. The package includes a compiled frontend for the combined app and reproducible source/lockfiles, but excludes database contents and local credentials.

## Repository layout

At the user's publication request, the frontend was moved to the repository's top-level `frontend/` folder. The backend remains in `v2/`. Startup, production asset serving, browser-test paths and OpenAPI type generation follow this layout. Git excludes installed dependencies, local environment files, generated builds and runtime/test logs.
