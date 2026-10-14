from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import Availability, CreditEntry, User, UserSkill


def test_repeatable_seed_and_evaluation(client, monkeypatch):
    from app.cli import seed

    monkeypatch.setenv("DEMO_PASSWORD", "Strong-Synthetic-Demo-Password")
    seed()
    seed()
    with Session(get_engine()) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 15
        assert (
            db.scalar(
                select(func.count()).select_from(CreditEntry).where(CreditEntry.kind == "GRANT")
            )
            == 15
        )
        assert (
            db.scalar(
                select(func.count()).select_from(CreditEntry).where(CreditEntry.kind == "TRANSFER")
            )
            == 1
        )

    def login(email):
        token = client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": "Strong-Synthetic-Demo-Password"},
        ).json()["access_token"]
        return {"Authorization": "Bearer " + token}

    admin = login("admin@example.com")
    learner = login("learner@example.com")
    request = client.get("/api/v1/requests", headers=learner).json()["items"][0]
    result = client.get("/api/v1/admin/evaluation/requests/" + request["id"], headers=admin)
    assert result.status_code == 200, result.text
    assert len(result.json()["models"]) == 3
    assert client.get("/api/v1/admin/evaluation/outcomes", headers=learner).status_code == 403
    assert (
        client.get("/api/v1/admin/evaluation/outcomes", headers=admin).json()["completed_sessions"]
        == 1
    )


def test_password_whitespace_is_preserved(client):
    payload = {
        "name": "Space",
        "email": "space@example.com",
        "password": "  Strong-Password-With-Spaces  ",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert (
        client.post(
            "/api/v1/auth/token",
            data={"username": payload["email"], "password": payload["password"]},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/token",
            data={"username": payload["email"], "password": payload["password"].strip()},
        ).status_code
        == 401
    )


def test_extra_members_can_teach_and_learn_without_duplicate_credits(client, monkeypatch):
    from app.cli import seed

    password = "Strong-Synthetic-Demo-Password"
    monkeypatch.setenv("DEMO_PASSWORD", password)
    seed(extra_members=20)
    seed(extra_members=20)
    with Session(get_engine()) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 35
        assert (
            db.scalar(
                select(func.count()).select_from(CreditEntry).where(CreditEntry.kind == "GRANT")
            )
            == 35
        )
        for i in range(1, 21):
            user = db.scalar(select(User).where(User.email == f"member{i:02d}@example.com"))
            assert user is not None and not user.is_admin
            for kind in ["OFFER", "WANT"]:
                assert (
                    db.scalar(
                        select(func.count())
                        .select_from(UserSkill)
                        .where(UserSkill.user_id == user.id, UserSkill.kind == kind)
                    )
                    == 2
                )
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(Availability)
                    .where(Availability.user_id == user.id)
                )
                == 2
            )
    for email in ["member01@example.com", "member10@example.com", "member20@example.com"]:
        response = client.post("/api/v1/auth/token", data={"username": email, "password": password})
        assert response.status_code == 200, "Expanded demo account could not log in"


def test_same_account_can_book_learning_and_accept_teaching(client, monkeypatch):
    from app.cli import seed

    password = "Strong-Synthetic-Demo-Password"
    monkeypatch.setenv("DEMO_PASSWORD", password)
    seed(extra_members=3)
    members = []
    for i in range(1, 4):
        login = client.post(
            "/api/v1/auth/token",
            data={"username": f"member{i:02d}@example.com", "password": password},
        )
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        members.append((client.get("/api/v1/me", headers=headers).json(), headers))
    person, person_headers = members[0]
    provider, provider_headers = members[1]
    learner, learner_headers = members[2]
    with Session(get_engine()) as db:
        start = db.scalar(
            select(Availability.starts_at).where(Availability.user_id == person["id"])
        )
    catalog = {
        s["name"]: s["id"]
        for s in client.get("/api/v1/skills", headers=person_headers).json()["items"]
    }

    def book(skill, buyer, buyer_headers, seller, seller_headers, begins):
        request = client.post(
            "/api/v1/requests",
            headers=buyer_headers,
            json={
                "skill_id": catalog[skill],
                "duration_minutes": 1,
                "window_start": begins.isoformat(),
                "window_end": (begins + timedelta(hours=1)).isoformat(),
                "mode": "ONLINE",
            },
        ).json()
        path = "/api/v1/requests/" + request["id"]
        candidates = client.post(path + "/matches", headers=buyer_headers).json()["candidates"]
        candidate = next(c for c in candidates if c["provider_id"] == seller["id"])
        assert (
            client.post(
                path + "/select", headers=buyer_headers, json={"candidate_id": candidate["id"]}
            ).status_code
            == 200
        )
        session = client.post(path + "/accept", headers=seller_headers)
        assert session.status_code == 200, session.text
        return session.json()

    learning = book("Python", person, person_headers, provider, provider_headers, start)
    teaching = book(
        "React", learner, learner_headers, person, person_headers, start + timedelta(hours=2)
    )
    assert learning["learner_id"] == teaching["provider_id"] == person["id"]
    listed = client.get("/api/v1/sessions", headers=person_headers).json()["items"]
    assert {s["id"] for s in listed} == {learning["id"], teaching["id"]}


def test_extra_demo_accounts_do_not_overwrite_existing_users(client, monkeypatch):
    from app.cli import seed
    from tests.conftest import register

    user, headers = register(client, "Existing Member", "member01@example.com")
    monkeypatch.setenv("DEMO_PASSWORD", "Different-Synthetic-Demo-Password")
    with pytest.raises(ValueError, match="non-demo account"):
        seed(extra_members=1)
    assert client.get("/api/v1/me", headers=headers).json()["name"] == "Existing Member"
    with Session(get_engine()) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1
