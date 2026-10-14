from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import CreditEntry, ExchangeSession
from tests.conftest import register
from tests.test_matching import setup_exchange
from tests.test_sessions import booked


def test_competing_bookings_cannot_double_reserve_or_overlap(client):
    learner, lh, teacher, th, root, child, req = setup_exchange(client, 90)
    second_payload = {
        key: req[key]
        for key in ["skill_id", "duration_minutes", "window_start", "window_end", "mode"]
    }
    other = client.post("/api/v1/requests", headers=lh, json=second_payload).json()
    for request in [req, other]:
        path = "/api/v1/requests/" + request["id"]
        candidate = client.post(path + "/matches", headers=lh).json()["candidates"][0]
        assert (
            client.post(
                path + "/select", headers=lh, json={"candidate_id": candidate["id"]}
            ).status_code
            == 200
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda request: client.post(
                    "/api/v1/requests/" + request["id"] + "/accept", headers=th
                ),
                [req, other],
            )
        )
    assert sorted(response.status_code for response in responses) == [200, 409]
    balance = client.get("/api/v1/me/wallet", headers=lh).json()
    assert balance["reserved_minutes"] == 90
    assert balance["available_minutes"] == 30
    with Session(get_engine()) as db:
        assert db.scalar(select(func.count()).select_from(ExchangeSession)) == 1


def test_ledger_cannot_be_edited_even_with_direct_sql(client):
    user, headers = register(client)
    with Session(get_engine()) as db:
        entry_id = db.scalar(select(CreditEntry.id).where(CreditEntry.receiver_id == user["id"]))
        with pytest.raises(IntegrityError):
            db.execute(text("UPDATE credit_ledger SET minutes=9999 WHERE id=:id"), {"id": entry_id})
        db.rollback()
        assert db.get(CreditEntry, entry_id).minutes == 120


def test_removed_offer_cannot_be_accepted_from_old_match(client):
    learner, lh, teacher, th, root, child, req = setup_exchange(client)
    path = "/api/v1/requests/" + req["id"]
    candidate = client.post(path + "/matches", headers=lh).json()["candidates"][0]
    client.post(path + "/select", headers=lh, json={"candidate_id": candidate["id"]})
    client.delete("/api/v1/me/skills/" + child["id"] + "/OFFER", headers=th)
    result = client.post(path + "/accept", headers=th)
    assert result.status_code == 409
    assert result.json()["error"]["code"] == "SLOT_UNAVAILABLE"


def test_notification_ownership_and_invalid_token(client):
    learner, lh, teacher, th, session = booked(client)
    notification = client.get("/api/v1/notifications", headers=th).json()["items"][0]
    assert (
        client.post("/api/v1/notifications/" + notification["id"] + "/read", headers=lh).status_code
        == 404
    )
    assert (
        client.post("/api/v1/notifications/" + notification["id"] + "/read", headers=th).json()[
            "is_read"
        ]
        is True
    )
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_auth_throttle_and_safe_error_body(client):
    user, headers = register(client)
    for _ in range(19):
        response = client.post(
            "/api/v1/auth/token", data={"username": "learner@example.com", "password": "incorrect"}
        )
        assert response.status_code == 401
    response = client.post(
        "/api/v1/auth/token", data={"username": "learner@example.com", "password": "incorrect"}
    )
    assert response.status_code == 429
    assert "incorrect" not in response.text


def test_reversal_cannot_spend_another_session_reservation(client, monkeypatch):
    from tests.test_trust import complete

    learner, lh, teacher, th, session = complete(client, monkeypatch)
    # Simulate the provider's balance already being reserved elsewhere by using real API bookings.
    third, third_headers = register(client, "Third", "third@example.com")
    client.put(
        "/api/v1/me/skills",
        headers=third_headers,
        json={"skill_id": session["skill_id"], "kind": "OFFER", "level": 5},
    )
    start = datetime.fromisoformat(session["ends_at"]) + timedelta(days=1)
    client.post(
        "/api/v1/me/availability",
        headers=third_headers,
        json={
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=3)).isoformat(),
            "mode": "ONLINE",
        },
    )
    req = client.post(
        "/api/v1/requests",
        headers=th,
        json={
            "skill_id": session["skill_id"],
            "duration_minutes": 150,
            "window_start": start.isoformat(),
            "window_end": (start + timedelta(hours=3)).isoformat(),
            "mode": "ONLINE",
        },
    ).json()
    path = "/api/v1/requests/" + req["id"]
    candidate = client.post(path + "/matches", headers=th).json()["candidates"][0]
    client.post(path + "/select", headers=th, json={"candidate_id": candidate["id"]})
    assert client.post(path + "/accept", headers=third_headers).status_code == 200
    dispute = client.post(
        "/api/v1/sessions/" + session["id"] + "/disputes",
        headers=lh,
        json={"reason": "Correction requested by both participants"},
    ).json()
    result = client.post(
        "/api/v1/admin/disputes/" + dispute["id"] + "/resolve",
        headers=lh,
        json={"action": "REVERSE", "note": "Both parties confirmed the requested correction"},
    )
    assert result.status_code == 409
    assert result.json()["error"]["code"] == "REVERSAL_INSUFFICIENT_CREDITS"
    assert (
        client.get("/api/v1/sessions/" + session["id"], headers=lh).json()["status"] == "DISPUTED"
    )
