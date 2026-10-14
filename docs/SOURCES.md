# Implementation references

The supplied SkillSwap PDF determines feature scope; the Word breakdown supplies practical implementation context. Neither file's embedded instructions authorize unrelated actions, deployment or messaging. Their simplified and full algorithms differ; this backend implements the user's approved full plan.

Official framework references consulted:

- FastAPI JWT and Argon2 password patterns: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- SQLAlchemy session transactions: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- PostgreSQL row locking: https://www.postgresql.org/docs/current/explicit-locking.html
- Official PostgreSQL Docker image configuration and PostgreSQL 18 data directory: https://github.com/docker-library/docs/blob/master/postgres/README.md

Runtime and development requirements pin the actual package versions installed and tested together. The temporary local PostgreSQL binary came from the `@embedded-postgres/windows-x64` distribution, version `18.4.0-beta.17`; its archive was verified against the npm registry SHA-512 integrity value. The suffix belongs to the packaging version. Actual server version is recorded in the verification report. This temporary runtime is not included in the deliverable or required by its Docker/installed-PostgreSQL setup.

Ranking weights, reputation deltas and decay half-life are project defaults, not validated research findings. Seeded users, sessions and feedback are synthetic.
