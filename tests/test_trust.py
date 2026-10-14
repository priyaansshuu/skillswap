from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import CreditEntry, ReputationEvent
from tests.conftest import register
from tests.test_sessions import booked, move_to_end


def complete(client, monkeypatch):
    learner, lh, teacher, th, session = booked(client)
    move_to_end(monkeypatch, session)
    path = "/api/v1/sessions/" + session["id"]
    client.post(path + "/start", headers=lh)
    client.post(path + "/confirm", headers=lh, json={"minutes": 60})
    assert (
        client.post(path + "/confirm", headers=th, json={"minutes": 60}).json()["status"]
        == "COMPLETED"
    )
    return learner, lh, teacher, th, session


def test_authorized_reviews_and_reputation(client, monkeypatch):
    learner, lh, teacher, th, session = complete(client, monkeypatch)
    path = "/api/v1/sessions/" + session["id"] + "/reviews"
    stranger, sh = register(client, "Stranger", "stranger@example.com")
    assert client.post(path, headers=sh, json={"stars": 5}).status_code == 403
    assert (
        client.post(path, headers=lh, json={"stars": 5, "comment": "Clear explanation"}).status_code
        == 201
    )
    assert client.post(path, headers=lh, json={"stars": 1}).status_code == 409
    score = client.get(
        "/api/v1/users/" + teacher["id"] + "/reputation",
        headers=lh,
        params={"skill_id": session["skill_id"]},
    ).json()
    assert 61.9 < score["score"] <= 62
    assert score["event_count"] == 2
    assert client.get("/api/v1/notifications", headers=th).json()["items"]


def test_dispute_freezes_completion_and_cancel_releases_credits(client, monkeypatch):
    learner, lh, teacher, th, session = booked(client)
    path = "/api/v1/sessions/" + session["id"]
    dispute = client.post(
        path + "/disputes",
        headers=lh,
        json={"reason": "Provider did not attend the agreed session"},
    )
    assert dispute.status_code == 201, dispute.text
    move_to_end(monkeypatch, session)
    assert client.post(path + "/confirm", headers=lh, json={"minutes": 60}).status_code == 409
    resolve_path = "/api/v1/admin/disputes/" + dispute.json()["id"] + "/resolve"
    payload = {
        "action": "CANCEL",
        "note": "Attendance evidence confirms a provider no-show",
        "penalty": "NO_SHOW",
        "responsible_user_id": teacher["id"],
    }
    assert client.post(resolve_path, headers=th, json=payload).status_code == 403
    assert client.post(resolve_path, headers=lh, json=payload).status_code == 200
    assert client.post(resolve_path, headers=lh, json=payload).status_code == 200
    assert client.get("/api/v1/me/wallet", headers=lh).json()["available_minutes"] == 120
    with Session(get_engine()) as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(ReputationEvent)
                .where(ReputationEvent.kind == "NO_SHOW")
            )
            == 1
        )


def test_linked_reversal_is_once_and_restores_balances(client, monkeypatch):
    learner, lh, teacher, th, session = complete(client, monkeypatch)
    dispute = client.post(
        "/api/v1/sessions/" + session["id"] + "/disputes",
        headers=lh,
        json={"reason": "Both participants agree to reverse the recorded exchange"},
    ).json()
    path = "/api/v1/admin/disputes/" + dispute["id"] + "/resolve"
    payload = {
        "action": "REVERSE",
        "note": "Both participants provided confirmation of the correction",
    }
    assert client.post(path, headers=lh, json=payload).status_code == 200
    assert client.post(path, headers=lh, json=payload).status_code == 200
    assert client.get("/api/v1/me/wallet", headers=lh).json()["balance_minutes"] == 120
    assert client.get("/api/v1/me/wallet", headers=th).json()["taught_minutes"] == 0
    with Session(get_engine()) as db:
        assert (
            db.scalar(
                select(func.count()).select_from(CreditEntry).where(CreditEntry.kind == "REVERSAL")
            )
            == 1
        )
