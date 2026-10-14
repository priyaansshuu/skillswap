# Changelog

## Blank demo accounts — 14 October 2026

- Added `seed --blank-members COUNT` for accounts without preset skills, learning goals, availability or profile location.
- Blank accounts use the same login and wallet for both teaching and learning.
- Repeated setup preserves skills and profile details added by the user.

## Additional demo members — 14 October 2026

- Added a repeatable `seed --extra-members COUNT` option for accounts that can both teach and learn.
- Each additional member receives teaching offers, learning goals, dated availability and the configured starter balance.
- Existing passwords and ledger history are preserved; non-demo address collisions roll back safely.
- Added tests proving one login can participate in both exchange roles.

## 0.1.0 — 14 October 2026

### Added

- Accounts, private profiles, offered skills, learning goals and dated availability.
- Explainable five-factor matching with nearest-ancestor fallback.
- Provider requests, scheduling, credit reservations and completion confirmed by both participants.
- Immutable credit history, cancellation refunds and linked reversals.
- Reviews, dated reputation, notifications, blocking and administrator dispute resolution.
- PostgreSQL migrations, integrity guards, synthetic demo data, API documentation and 27 automated tests.

This release targets local college demonstrations; no public deployment is included.
