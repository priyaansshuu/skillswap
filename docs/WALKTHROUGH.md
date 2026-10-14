# SkillSwap API walkthrough

Use Swagger at `/docs`; expand an endpoint and choose **Try it out**. IDs below come from API responses. All accounts and seed history are synthetic.

## Accounts and skill setup

`POST /api/v1/auth/register`: `{ "name": "Learner", "email": "learner@example.com", "password": "a strong password of your choice" }`.

`POST /api/v1/auth/token`: submit form fields `username` (email) and `password`. Use the returned bearer token. `GET /api/v1/me` shows private profile and balances; `PATCH /api/v1/me` changes name, city, campus and bio.

`GET /api/v1/skills` lists catalog entries. Administrators create and update catalog skills with `POST /skills` and `PUT /skills/{id}`. Ordinary users use `PUT /me/skills` with `{ "skill_id": "ID", "kind": "OFFER", "level": 4 }`; use `WANT` for a learning goal. Levels are 1-5. Delete an entry with `DELETE /me/skills/{skill_id}/{kind}`.

Teachers add dated availability using `POST /me/availability`. Supply offset-aware `starts_at`, `ends_at` and `mode` (`ONLINE` or `IN_PERSON`). Availability must start in the future. Removing availability does not cancel already accepted sessions.

## Discovery and booking

Create a request using `POST /requests` with a catalog skill ID, `duration_minutes`, `window_start`, `window_end`, and `mode`. The time window must fit the requested duration and cannot exceed 30 days.

`POST /requests/{id}/matches` stores a matching run and returns at most 50 candidates. Each candidate contains its ID, provider ID, offered skill, suggested start, hierarchy distance, factors and weighted score. Exact matches precede nearest-ancestor fallback; related skills are explicitly labeled, never presented as verified expertise in the requested skill.

`POST /requests/{id}/select`: `{ "candidate_id": "ID from that request's full matching result" }`. This sends the selected provider a notification. Only the learner can select. Selection itself reserves no credits.

The selected teacher uses `POST /requests/{id}/accept` or `/reject`. Acceptance rechecks availability, current offers, blocks, existing bookings and available credits. It atomically creates a scheduled session, reserves the learner's minutes and marks the request accepted. Repeating acceptance returns the same session.

## Completion and feedback

Either participant uses `POST /sessions/{id}/start` once its scheduled start has arrived. Before start, `/cancel` releases the reservation. After the scheduled start, cancellation requires administrator dispute resolution.

After the scheduled end, each participant sends `POST /sessions/{id}/confirm`: `{ "minutes": 50 }`. The duration must be positive and cannot exceed the reservation. Different confirmations leave the session in progress; either participant can correct their confirmation before settlement. `GET /sessions/{id}/confirmations` shows both submissions.

Equal confirmations transfer credits exactly once. Unused reserved minutes are released. Repeating the same completed duration succeeds; attempting to change it fails. `GET /me/wallet` and `/me/credits` expose balances and ledger history.

Each participant can submit one review with `POST /sessions/{id}/reviews`: `{ "stars": 5, "comment": "Clear explanation" }`. Reviews require a completed session. A learner's review affects the provider's skill-specific reputation; a provider's review affects the learner's overall reputation. Read `/users/{id}/reputation?skill_id=ID` for a skill score, or omit the skill for overall reputation.

## Disputes and notifications

`POST /sessions/{id}/disputes`: `{ "reason": "At least ten characters explaining the problem" }`. Completion freezes while an open dispute exists; existing settled credits remain unchanged pending resolution.

The administrator reads `/admin/disputes` and resolves with `/admin/disputes/{id}/resolve`. Actions are `DISMISS`, `CANCEL` (unsettled exchanges), and `REVERSE` (settled exchanges). Supply a note; optional verified penalties are `NO_SHOW` and `UNJUSTIFIED_CANCELLATION`, with a responsible participant ID. A report alone never causes a penalty.

A reversal inserts a linked opposite transfer. If the provider lacks unreserved credits, it fails safely and the dispute remains open. Reversed completion and review events no longer influence reputation, but separately verified penalties remain. Only one dispute per session is supported in this demo; a resolved dispute cannot be silently rewritten.

Notifications are available at `GET /notifications`; `POST /notifications/{id}/read` marks your own notification read. Blocking via `PUT /me/blocks/{user_id}` prevents new discovery and acceptance between those users. It does not silently cancel existing sessions.

## Evaluation

Admin-only `GET /admin/evaluation/requests/{id}` returns exact, skill-plus-reputation and full-model rankings with local query timings. `GET /admin/evaluation/outcomes` reports cumulative recorded counters with a synthetic-data caveat.

For a saved comparison, run:

```powershell
python -m app.cli evaluate REQUEST_ID --output docs/evaluation.json
```

Optional `--labels labels.json` accepts a JSON mapping from provider IDs to `true`/`false`. Every retrieved provider must have an explicit label. Precision@5 uses five as the denominator, including missing result positions. Relevance labels should be collected independently; labeling synthetic profiles for a demonstration does not validate the algorithm.
