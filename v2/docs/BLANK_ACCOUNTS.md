# Blank accounts for your own skill choices

20 additional blank accounts have been created in the local demo database. The 35 existing accounts are preserved (55 total). Each blank account uses one login and wallet for both teaching and learning, with the configured 120 starter minutes. No teaching offers, learning goals, availability, city, campus or bio have been filled in.

Sign in with the existing DEMO_PASSWORD from the local ignored `.env`. Passwords are not included in this list or the downloadable archive.

| Login | Teaching skills | Learning goals |
|---|---|---|
| blank01@example.com | None added | None added |
| blank02@example.com | None added | None added |
| blank03@example.com | None added | None added |
| blank04@example.com | None added | None added |
| blank05@example.com | None added | None added |
| blank06@example.com | None added | None added |
| blank07@example.com | None added | None added |
| blank08@example.com | None added | None added |
| blank09@example.com | None added | None added |
| blank10@example.com | None added | None added |
| blank11@example.com | None added | None added |
| blank12@example.com | None added | None added |
| blank13@example.com | None added | None added |
| blank14@example.com | None added | None added |
| blank15@example.com | None added | None added |
| blank16@example.com | None added | None added |
| blank17@example.com | None added | None added |
| blank18@example.com | None added | None added |
| blank19@example.com | None added | None added |
| blank20@example.com | None added | None added |

## Add your own skills

1. Log in as any blank account through the API documentation at `/docs`.
2. Use `GET /api/v1/skills` to choose a skill from the catalog.
3. Use `PUT /api/v1/me/skills` with that skill ID, `kind: OFFER` for a skill you teach, or `kind: WANT` for a skill you want to learn, and a level from 1 to 5. Both can be added to the same account.
4. Add your available times with `POST /api/v1/me/availability` when you are ready to teach.
5. If your chosen skill is not in the catalog, create it through the administrator account using `POST /api/v1/skills`, then select it from your blank account.

Example for teaching: `{"skill_id":"catalog skill ID","kind":"OFFER","level":4}`. For learning, change the kind to `WANT` and choose your desired level.

Recreate or expand the account set with `python -m app.cli seed --blank-members 20`. Increase the number to add more accounts, up to 200. Repeating this command does not erase your added skills, profile, password or credit history.
