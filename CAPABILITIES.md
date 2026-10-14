# SkillSwap capability map

| Module | Responsibility | Dependencies |
|---|---|---|
| identity | Accounts, authentication, profile and admin permissions | Database |
| catalog | Skill hierarchy, offers/goals, availability and blocks | identity |
| matching | Eligible ranked providers and explainable snapshots | catalog |
| exchange | Requests, scheduling and completion confirmations | matching |
| accounting | Reservations, immutable credits and reversals | exchange |
| trust | Reviews, reputation, disputes and notifications | accounting |
| demonstration | Seed data, evaluation and DBMS evidence | All |

Build in this order. Accounting is invoked inside exchange transactions, not as a separate service.
The user approved FastAPI/PostgreSQL, full PDF scope, starter credits, dual completion and local demo.
