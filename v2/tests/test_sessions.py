from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import Confirmation, CreditEntry, Notification, ReputationEvent
from tests.test_matching import setup_exchange


def booked(client, duration=60):
    learner, lh, teacher, th, root, child, request = setup_exchange(client, duration)
    matches = client.post("/api/v1/requests/" + request["id"] + "/matches", headers=lh).json()
    selected = client.post(
        "/api/v1/requests/" + request["id"] + "/select",
        headers=lh,
        json={"candidate_id": matches["candidates"][0]["id"]},
    )
    assert selected.status_code == 200, selected.text
    response = client.post("/api/v1/requests/" + request["id"] + "/accept", headers=th)
    assert response.status_code == 200, response.text
    return learner, lh, teacher, th, response.json()


def move_to_end(monkeypatch, session):
    from datetime import datetime

    monkeypatch.setattr(
        "app.sessions.now",
        lambda: datetime.fromisoformat(session["ends_at"]) + timedelta(minutes=1),
    )


def test_dual_completion_mismatch_and_retry(client, monkeypatch):
    learner, lh, teacher, th, session = booked(client)
    path = "/api/v1/sessions/" + session["id"]
    assert client.get("/api/v1/me/wallet", headers=lh).json()["available_minutes"] == 60
    assert client.post(path + "/confirm", headers=lh, json={"minutes": 60}).status_code == 409
    move_to_end(monkeypatch, session)
    assert client.post(path + "/start", headers=th).status_code == 200
    assert (
        client.post(path + "/confirm", headers=lh, json={"minutes": 50}).json()["status"]
        == "IN_PROGRESS"
    )
    assert (
        client.post(path + "/confirm", headers=th, json={"minutes": 60}).json()["status"]
        == "IN_PROGRESS"
    )
    assert (
        client.post(path + "/confirm", headers=th, json={"minutes": 50}).json()["status"]
        == "COMPLETED"
    )
    assert client.post(path + "/confirm", headers=lh, json={"minutes": 50}).status_code == 200
    assert client.post(path + "/confirm", headers=lh, json={"minutes": 60}).status_code == 409
    assert client.get("/api/v1/me/wallet", headers=lh).json()["available_minutes"] == 70
    assert client.get("/api/v1/me/wallet", headers=th).json()["taught_minutes"] == 50
    assert client.get("/api/v1/me/wallet", headers=th).json()["balance_minutes"] == 170
    with Session(get_engine()) as db:
        assert (
            db.scalar(
                select(func.count()).select_from(CreditEntry).where(CreditEntry.kind == "TRANSFER")
            )
            == 1
        )


def test_cancellation_releases_hold(client):
    learner, lh, teacher, th, session = booked(client)
    path = "/api/v1/sessions/" + session["id"] + "/cancel"
    assert client.post(path, headers=th).json()["status"] == "CANCELLED"
    assert client.post(path, headers=lh).status_code == 200
    assert client.get("/api/v1/me/wallet", headers=lh).json()["available_minutes"] == 120


def test_insufficient_credit_at_acceptance(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client, 121)
    # Extend teacher availability so lack of credit is the only failing condition.
    start = request["window_start"]
    from datetime import datetime

    client.post(
        "/api/v1/me/availability",
        headers=th,
        json={
            "starts_at": start,
            "ends_at": (datetime.fromisoformat(start) + timedelta(hours=3)).isoformat(),
            "mode": "ONLINE",
        },
    )
    candidate = client.post("/api/v1/requests/" + request["id"] + "/matches", headers=lh).json()[
        "candidates"
    ][0]
    client.post(
        "/api/v1/requests/" + request["id"] + "/select",
        headers=lh,
        json={"candidate_id": candidate["id"]},
    )
    response = client.post("/api/v1/requests/" + request["id"] + "/accept", headers=th)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_CREDITS"


def test_simultaneous_confirmations_transfer_once(client, monkeypatch):
    learner, lh, teacher, th, session = booked(client)
    move_to_end(monkeypatch, session)
    path = "/api/v1/sessions/" + session["id"]
    client.post(path + "/start", headers=th)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda h: client.post(path + "/confirm", headers=h, json={"minutes": 60}), [lh, th]
            )
        )
    assert all(r.status_code == 200 for r in results)
    with Session(get_engine()) as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(CreditEntry)
                .where(CreditEntry.session_id == session["id"], CreditEntry.kind == "TRANSFER")
            )
            == 1
        )
    assert client.get("/api/v1/me/wallet", headers=lh).json()["balance_minutes"] == 60


def test_settlement_failure_rolls_back_everything(client, monkeypatch):
    learner, lh, teacher, th, session = booked(client)
    move_to_end(monkeypatch, session)
    path = "/api/v1/sessions/" + session["id"]
    client.post(path + "/start", headers=th)
    client.post(path + "/confirm", headers=lh, json={"minutes": 60})

    with Session(get_engine()) as db:
        before_notifications = db.scalar(select(func.count()).select_from(Notification))

    def broken_notification(*args, **kwargs):
        raise RuntimeError("Injected failure after ledger flush")

    monkeypatch.setattr("app.sessions.notify", broken_notification)
    response = client.post(path + "/confirm", headers=th, json={"minutes": 60})
    assert response.status_code == 500
    assert client.get(path, headers=lh).json()["status"] == "IN_PROGRESS"
    balance = client.get("/api/v1/me/wallet", headers=lh).json()
    assert balance["balance_minutes"] == 120
    assert balance["reserved_minutes"] == 60
    with Session(get_engine()) as db:
        assert not db.scalar(select(CreditEntry.id).where(CreditEntry.session_id == session["id"]))
        assert not db.scalar(
            select(ReputationEvent.id).where(ReputationEvent.session_id == session["id"])
        )
        assert db.get(Confirmation, (session["id"], teacher["id"])) is None
        assert db.scalar(select(func.count()).select_from(Notification)) == before_notifications
