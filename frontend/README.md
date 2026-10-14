# SkillSwap frontend

React + TypeScript + Vite, React Router, TanStack Query, Lucide icons, and locally bundled Nunito Sans. This top-level frontend consumes the FastAPI backend in ../v2/; it contains no database credentials.

```powershell
npm ci
npm run dev
```

Development URL: http://127.0.0.1:5173. API requests are proxied to http://127.0.0.1:8000. The approved production demo builds with `npm run build` and is served by FastAPI on port 8000.

- `npm test`: focused authentication/client and form tests.
- `npm run build`: strict TypeScript checks and production bundle.
- `npm run types:generate`: regenerate response types from ../v2/docs/openapi.json, then format the generated file.
- From ../v2/, run `python scripts/run_browser_checks.py`; see ../v2/docs/FRONTEND_DEMO.md for the isolated PostgreSQL browser checks.

Feature boundaries: discovery, account setup, dashboard, requests, sessions, credits, notifications, and administration. Server data belongs to TanStack Query; search filters belong to the URL; unfinished form values are component state. Auth uses a 30-minute per-tab session and clears cached private records on logout/expiry. API response types are generated; request bodies remain validated by FastAPI.

The approved mockups are in ../v2/.impeccable/mocks/. Runtime screenshots and verification records are separate.
