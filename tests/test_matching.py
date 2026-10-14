from datetime import timedelta
from types import SimpleNamespace

import pytest

from app.models import now
from tests.conftest import register
from tests.test_catalog import make_admin


def setup_exchange(client, duration=60):
    learner, lh = register(client)
    teacher, th = register(client, "Teacher", "teacher@example.com")
    make_admin(learner["id"])
    root = client.post(
        "/api/v1/skills", headers=lh, json={"name": "JavaScript", "category": "Tech"}
    ).json()
    child = client.post(
        "/api/v1/skills",
        headers=lh,
        json={"name": "React", "category": "Tech", "parent_id": root["id"]},
    ).json()
    assert (
        client.put(
            "/api/v1/me/skills",
            headers=th,
            json={"skill_id": child["id"], "kind": "OFFER", "level": 4},
        ).status_code
        == 200
    )
    start = now() + timedelta(days=1)
    slot = {
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=2)).isoformat(),
        "mode": "ONLINE",
    }
    assert client.post("/api/v1/me/availability", headers=th, json=slot).status_code == 201
    payload = {
        "skill_id": child["id"],
        "duration_minutes": duration,
        "window_start": start.isoformat(),
        "window_end": (start + timedelta(hours=3)).isoformat(),
        "mode": "ONLINE",
    }
    response = client.post("/api/v1/requests", headers=lh, json=payload)
    assert response.status_code == 201, response.text
    return learner, lh, teacher, th, root, child, response.json()


def test_exact_fallback_and_blocked_candidates(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    path = "/api/v1/requests/" + request["id"] + "/matches"
    exact = client.post(path, headers=lh)
    assert exact.status_code == 200, exact.text
    candidate = exact.json()["candidates"][0]
    assert candidate["provider_id"] == teacher["id"]
    assert candidate["hierarchy_distance"] == 0
    assert candidate["factors"]["skill"] == 1
    assert client.post(path, headers=th).status_code == 403
    client.delete("/api/v1/me/skills/" + child["id"] + "/OFFER", headers=th)
    client.put(
        "/api/v1/me/skills", headers=th, json={"skill_id": root["id"], "kind": "OFFER", "level": 4}
    )
    fallback = client.post(path, headers=lh).json()["candidates"][0]
    assert fallback["hierarchy_distance"] == 1
    assert fallback["factors"]["skill"] == 0.8
    client.put("/api/v1/me/blocks/" + teacher["id"], headers=lh)
    assert client.post(path, headers=lh).json()["candidates"] == []


def test_reputation_decay_and_cold_start():
    from app.reputation import decayed_score

    timestamp = now()
    assert decayed_score([], timestamp, 90) == 50
    events = [SimpleNamespace(created_at=timestamp, delta=2)]
    assert decayed_score(events, timestamp, 90) == 52
    assert decayed_score(events, timestamp + timedelta(days=90), 90) == pytest.approx(26)


def test_unavailable_and_missing_skills(client):
    learner, lh = register(client)
    assert (
        client.post(
            "/api/v1/requests",
            headers=lh,
            json={
                "skill_id": "missing",
                "duration_minutes": 60,
                "window_start": (now() + timedelta(days=1)).isoformat(),
                "window_end": (now() + timedelta(days=1, hours=2)).isoformat(),
                "mode": "ONLINE",
            },
        ).status_code
        == 404
    )
