from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import ExchangeRequest, MatchRun, Notification, now
from tests.conftest import register
from tests.test_matching import setup_exchange


def direct_payload(request, teacher):
    return {
        k: request[k]
        for k in ("skill_id", "duration_minutes", "window_start", "window_end", "mode")
    } | {"provider_id": teacher["id"]}


def test_public_discovery_is_sanitized_and_honors_blocks(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    member, mh = register(client, "Blank", "blank@example.com")
    response = client.get("/api/v1/public/providers", params={"skill_id": child["id"]})
    assert response.status_code == 200, response.text
    rows = response.json()["items"]
    assert [row["id"] for row in rows] == [teacher["id"]]
    assert rows[0]["rating_count"] == 0 and rows[0]["rating_average"] is None
    assert rows[0]["modes"] == ["ONLINE"]
    assert not {"email", "password_hash", "balance_minutes", "learning_goals"} & rows[0].keys()
    assert client.get("/api/v1/public/providers/" + member["id"]).status_code == 404
    assert client.get("/api/v1/public/skills").status_code == 200
    client.put("/api/v1/me/blocks/" + teacher["id"], headers=lh)
    assert client.get("/api/v1/public/providers", headers=lh).json()["items"] == []
    assert client.get("/api/v1/public/providers/" + teacher["id"], headers=lh).status_code == 404


def test_preview_has_no_persistence_and_requires_login(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    payload = direct_payload(request, teacher)
    assert client.post("/api/v1/requests/preview", json=payload).status_code == 401
    with Session(get_engine()) as db:
        before = [
            db.scalar(select(func.count()).select_from(m)) for m in (ExchangeRequest, MatchRun)
        ]
    response = client.post("/api/v1/requests/preview", headers=lh, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["eligible"] is True
    assert response.json()["candidates"][0]["provider"]["id"] == teacher["id"]
    with Session(get_engine()) as db:
        after = [
            db.scalar(select(func.count()).select_from(m)) for m in (ExchangeRequest, MatchRun)
        ]
    assert after == before


def test_direct_request_is_atomic_and_idempotent_under_concurrency(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    payload = direct_payload(request, teacher)
    headers = lh | {"Idempotency-Key": "frontend-transaction-001"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda _: client.post("/api/v1/requests", headers=headers, json=payload), range(2)
            )
        )
    assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
    assert responses[0].json()["id"] == responses[1].json()["id"]
    assert responses[0].json()["status"] == "REQUESTED"
    with Session(get_engine()) as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.resource_id == responses[0].json()["id"])
            )
            == 1
        )
    changed = payload | {"duration_minutes": 30}
    assert client.post("/api/v1/requests", headers=headers, json=changed).status_code == 409


def test_direct_request_revalidates_credits_slot_and_blocks(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    payload = direct_payload(request, teacher)
    assert (
        client.post(
            "/api/v1/requests", headers=lh, json=payload | {"duration_minutes": 180}
        ).status_code
        == 409
    )
    client.put("/api/v1/me/blocks/" + teacher["id"], headers=lh)
    assert client.post("/api/v1/requests", headers=lh, json=payload).status_code == 409
    assert (
        client.post("/api/v1/requests/preview", headers=lh, json=payload).json()["eligible"]
        is False
    )
    assert (
        client.post(
            "/api/v1/requests/preview",
            headers=lh,
            json=payload | {"window_start": (now() - timedelta(hours=1)).isoformat()},
        ).status_code
        == 422
    )


def test_skill_suggestion_approval_is_admin_only_and_notifies(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    response = client.post(
        "/api/v1/skill-suggestions",
        headers=th,
        json={"name": "Origami", "explanation": "I would like to teach paper folding."},
    )
    assert response.status_code == 201, response.text
    suggestion = response.json()
    assert client.get("/api/v1/admin/skill-suggestions", headers=th).status_code == 403
    path = "/api/v1/admin/skill-suggestions/" + suggestion["id"] + "/resolve"
    decision = {
        "action": "APPROVE",
        "name": "Origami",
        "category": "Arts",
        "note": "Approved for the community.",
    }
    assert client.post(path, headers=th, json=decision).status_code == 403
    approved = client.post(path, headers=lh, json=decision)
    assert approved.status_code == 200, approved.text
    assert client.post(path, headers=lh, json=decision).json() == approved.json()
    skill_id = approved.json()["skill_id"]
    assert (
        client.put(
            "/api/v1/me/skills",
            headers=th,
            json={"skill_id": skill_id, "kind": "OFFER", "level": 3},
        ).status_code
        == 200
    )
    assert client.get("/api/v1/skill-suggestions", headers=lh).json()["items"] == []
    assert any(
        n["resource_id"] == suggestion["id"]
        for n in client.get("/api/v1/notifications", headers=th).json()["items"]
    )
    assert client.get("/api/v1/admin/users", headers=th).status_code == 403
    assert len(client.get("/api/v1/admin/users", headers=lh).json()["items"]) == 2


def test_teaching_ratings_do_not_expose_private_review_text(client, monkeypatch):
    from tests.test_sessions import booked, move_to_end

    learner, lh, teacher, th, session = booked(client)
    move_to_end(monkeypatch, session)
    path = "/api/v1/sessions/" + session["id"]
    client.post(path + "/start", headers=th)
    client.post(path + "/confirm", headers=lh, json={"minutes": 60})
    client.post(path + "/confirm", headers=th, json={"minutes": 60})
    client.post(
        path + "/reviews", headers=lh, json={"stars": 4, "comment": "Private participant feedback."}
    )
    client.post(
        path + "/reviews", headers=th, json={"stars": 2, "comment": "Private learner review."}
    )
    profile = client.get("/api/v1/public/providers/" + teacher["id"])
    assert profile.status_code == 200, profile.text
    assert profile.json()["rating_count"] == 1
    assert profile.json()["rating_average"] == 4
    assert "Private" not in profile.text
    assert client.get(path + "/reviews").status_code == 401
    assert client.get("/api/v1/admin/sessions/" + session["id"], headers=th).status_code == 403
    assert client.get("/api/v1/admin/sessions/" + session["id"], headers=lh).status_code == 200


def test_request_role_filter_and_block_management_are_account_scoped(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    response = client.post("/api/v1/requests", headers=lh, json=direct_payload(request, teacher))
    assert response.status_code == 201, response.text
    assert len(client.get("/api/v1/requests?role=teaching", headers=th).json()["items"]) == 1
    assert client.get("/api/v1/requests?role=teaching", headers=lh).json()["items"] == []
    assert len(client.get("/api/v1/requests?role=learning", headers=lh).json()["items"]) == 2
    assert client.get("/api/v1/requests?role=learning", headers=th).json()["items"] == []
    client.put("/api/v1/me/blocks/" + teacher["id"], headers=lh)
    rows = client.get("/api/v1/me/blocks", headers=lh).json()["items"]
    assert [row["id"] for row in rows] == [teacher["id"]]
    assert "email" not in rows[0]
    assert client.get("/api/v1/me/blocks", headers=th).json()["items"] == []
    assert client.get("/api/v1/me/blocks").status_code == 401


def test_suggestion_rejection_duplicate_and_conflicting_resolution(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    response = client.post("/api/v1/skill-suggestions", headers=th, json={"name": "Origami"})
    assert response.status_code == 201, response.text
    duplicate = client.post("/api/v1/skill-suggestions", headers=th, json={"name": "origami"})
    assert duplicate.json()["id"] == response.json()["id"]
    path = "/api/v1/admin/skill-suggestions/" + response.json()["id"] + "/resolve"
    decision = {"action": "REJECT", "note": "Please clarify the proposed skill."}
    rejected = client.post(path, headers=lh, json=decision)
    assert rejected.json()["status"] == "REJECTED"
    assert client.post(path, headers=lh, json=decision).status_code == 200
    assert (
        client.post(
            path, headers=lh, json=decision | {"note": "A different rejection note."}
        ).status_code
        == 409
    )
