from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import Availability, CreditEntry, User, UserSkill


def login(client, email, password):
    response = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200, "Blank account could not log in"
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_blank_accounts_have_no_skills_goals_or_availability(client, monkeypatch):
    from app.cli import seed

    password = "Strong-Synthetic-Demo-Password"
    monkeypatch.setenv("DEMO_PASSWORD", password)
    seed(blank_members=20)
    seed(blank_members=20)
    with Session(get_engine()) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 35
        assert (
            db.scalar(
                select(func.count()).select_from(CreditEntry).where(CreditEntry.kind == "GRANT")
            )
            == 35
        )
        for i in range(1, 21):
            user = db.scalar(select(User).where(User.email == f"blank{i:02d}@example.com"))
            assert user is not None and not user.is_admin
            assert user.city is None and user.campus is None and user.bio == ""
            assert not db.scalar(select(UserSkill.skill_id).where(UserSkill.user_id == user.id))
            assert not db.scalar(select(Availability.id).where(Availability.user_id == user.id))
    for email in ["blank01@example.com", "blank20@example.com"]:
        headers = login(client, email, password)
        assert client.get("/api/v1/me/skills", headers=headers).json()["items"] == []
        assert client.get("/api/v1/me/availability", headers=headers).json()["items"] == []
        assert client.get("/api/v1/me/wallet", headers=headers).json()["available_minutes"] == 120


def test_blank_account_accepts_teaching_and_learning_choices_and_preserves_them(
    client, monkeypatch
):
    from app.cli import seed

    password = "Strong-Synthetic-Demo-Password"
    monkeypatch.setenv("DEMO_PASSWORD", password)
    seed(blank_members=2)
    headers = login(client, "blank01@example.com", password)
    catalog = {
        s["name"]: s["id"] for s in client.get("/api/v1/skills", headers=headers).json()["items"]
    }
    for kind, skill in [("OFFER", "Guitar"), ("WANT", "Python")]:
        result = client.put(
            "/api/v1/me/skills",
            headers=headers,
            json={"skill_id": catalog[skill], "kind": kind, "level": 3},
        )
        assert result.status_code == 200
    seed(blank_members=2)
    choices = client.get("/api/v1/me/skills", headers=headers).json()["items"]
    assert {(c["kind"], c["skill_id"]) for c in choices} == {
        ("OFFER", catalog["Guitar"]),
        ("WANT", catalog["Python"]),
    }
    other = login(client, "blank02@example.com", password)
    assert client.get("/api/v1/me/skills", headers=other).json()["items"] == []
