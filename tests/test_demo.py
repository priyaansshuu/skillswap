from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import CreditEntry, User


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
