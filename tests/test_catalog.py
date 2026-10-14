from datetime import timedelta

from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import User, now
from tests.conftest import register


def make_admin(user_id):
    with Session(get_engine()) as db:
        db.get(User, user_id).is_admin = True
        db.commit()


def test_skills_availability_and_admin_permissions(client):
    user, headers = register(client)
    assert (
        client.post(
            "/api/v1/skills", headers=headers, json={"name": "Python", "category": "Programming"}
        ).status_code
        == 403
    )
    make_admin(user["id"])
    skill = client.post(
        "/api/v1/skills", headers=headers, json={"name": "Python", "category": "Programming"}
    )
    assert skill.status_code == 201, skill.text
    offered = {"skill_id": skill.json()["id"], "kind": "OFFER", "level": 4}
    assert client.put("/api/v1/me/skills", headers=headers, json=offered).status_code == 200
    assert len(client.get("/api/v1/me/skills", headers=headers).json()["items"]) == 1
    start = now() + timedelta(days=1)
    slot = {
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=2)).isoformat(),
        "mode": "ONLINE",
    }
    response = client.post("/api/v1/me/availability", headers=headers, json=slot)
    assert response.status_code == 201, response.text
    stranger, stranger_headers = register(client, "Stranger", "stranger@example.com")
    assert (
        client.delete(
            "/api/v1/me/availability/" + response.json()["id"], headers=stranger_headers
        ).status_code
        == 404
    )
    public = client.get("/api/v1/users/" + user["id"], headers=stranger_headers)
    assert "email" not in public.json()
    assert client.put("/api/v1/me/blocks/" + stranger["id"], headers=headers).status_code == 204
    assert client.get("/api/v1/users/" + user["id"], headers=stranger_headers).status_code == 404


def test_skill_cycles_and_timezone_validation(client):
    user, headers = register(client)
    make_admin(user["id"])
    root = client.post(
        "/api/v1/skills", headers=headers, json={"name": "Web", "category": "Tech"}
    ).json()
    child = client.post(
        "/api/v1/skills",
        headers=headers,
        json={"name": "JS", "category": "Tech", "parent_id": root["id"]},
    ).json()
    assert (
        client.put(
            "/api/v1/skills/" + root["id"],
            headers=headers,
            json={"name": "Web", "category": "Tech", "parent_id": child["id"]},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/v1/me/availability",
            headers=headers,
            json={
                "starts_at": "2027-01-01T10:00:00",
                "ends_at": "2027-01-01T11:00:00",
                "mode": "ONLINE",
            },
        ).status_code
        == 422
    )
