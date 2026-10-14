# SkillSwap verification report

Verified locally on 14 October 2026 with Python 3.12.14 and PostgreSQL 18.4. All account, exchange and feedback data used for verification was synthetic.

## Executed checks

| Check | Result |
|---|---|
| Automated suite against real PostgreSQL | **32 passed** after adding dual-purpose and blank demo accounts; no skipped tests or warnings in the final run |
| Registration, login, private profile and starter credits | Passed |
| Invalid/expired JWT, suspended account and login throttling | Passed |
| Admin-only catalog changes, skill-cycle prevention and dated availability | Passed |
| Private profile fields, blocked discovery and notification ownership | Passed |
| Exact matching, nearest-ancestor fallback and unavailable providers | Passed |
| Cross-request candidate injection and removed-offer acceptance | Rejected correctly |
| Insufficient credits and cancellation refunds | Passed |
| Differing duration confirmations and repeated settlement | Passed |
| Two simultaneous completion confirmations | One transfer, correct final balances |
| Competing bookings | One accepted; no duplicate reservation or overlapping session |
| Failure injected after ledger/reputation insertion | Ledger, reputation, confirmation, notification, reservation and session changes rolled back |
| Direct SQL update of immutable ledger | PostgreSQL rejected it |
| Authorized reviews, rating bounds and reputation decay | Passed |
| Dispute freeze, verified penalties, administrator resolution and retry | Passed |
| Linked reversal and protection of other reserved credits | Passed |
| Request body size limit and browser-readable error | Passed |
| Repeatable seed | 15 accounts, 15 starter grants and one historical transfer after two runs |
| Expanded member seed | 20 additional accounts with teaching offers and learning goals; repeated seeding preserves one grant per account |
| One account in both roles | The same login booked a learning session and accepted a separate teaching session |
| Existing non-demo address collision | Seed rolled back without overwriting the existing user |
| Blank accounts | No skills, learning goals, availability, city, campus or bio prefilled; login and starter credits verified |
| Blank-account customization | Teaching offers and learning goals can be added to one account and survive repeated setup |
| Fresh migration, downgrade on disposable test database, re-upgrade | Passed |
| Alembic model/schema comparison | No new upgrade operations detected |
| Python compilation, Ruff lint and formatting | Passed |
| Installed package dependency consistency | No broken requirements |
| Runtime dependency audit through OSV | 32 pinned packages; no known vulnerabilities found |
| Live HTTP readiness, Swagger, login, matching, booking and cancellation | Passed; see `live-smoke.json` |
| Normal PostgreSQL restart persistence | Counts preserved; see `restart-persistence.json` |
| OpenAPI export | 48 documented API operations, explicit schemas and no exposed password hashes |

The dependency audit is a point-in-time advisory check, not a guarantee that no vulnerability exists. Its complete result is in `dependency-audit.json`. Only the runtime requirements were audited in that report.

## Review conclusions

Reviewed the implemented state transitions, participant/admin authorization, lock order, ledger constraints, retry behavior, score calculation and failure recovery. Balances are derived from immutable history rather than mutable cached totals. Every accounting writer serializes on participant rows before locking exchange records; unique ledger indexes provide an additional duplicate-settlement guard.

Final review corrected browser access to oversized-request errors, preserved password whitespace during registration, required the current migration at readiness, supplied concrete evaluation response schemas, and redacted raw validation inputs and database parameters from error surfaces. Regression tests cover the behavior changes where applicable.

## Practical limits

- Docker is not installed on this machine. Compose YAML and the PostgreSQL 18 volume layout were inspected, but the Linux container build/start path was **not executed**.
- Live HTTP checks exercised booking and cancellation. Full completion and reversal were exercised through the API test client connected to real PostgreSQL, using a controlled test clock. The normal running API enforces real session times.
- Persistence was checked through a normal server restart, not power loss or filesystem corruption.
- This is a local college-demo backend. It has not been deployed publicly or validated with real students.
- Ranking/reputation settings are proposed models. Synthetic rankings, seeded ratings and local timing measurements are not evidence of improved recommendation quality or user satisfaction.
