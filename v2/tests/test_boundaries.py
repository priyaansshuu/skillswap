from datetime import timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_engine
from app.models import Availability, User, now
from tests.conftest import register
from tests.test_matching import setup_exchange
from tests.test_sessions import booked, move_to_end


def test_expired_tokens_and_suspended_accounts(client):
    user, headers = register(client)
    token = jwt.encode(
        {
            "sub": user["id"],
            "iat": now() - timedelta(hours=1),
            "exp": now() - timedelta(minutes=30),
            "iss": "skillswap",
            "aud": "skillswap-api",
            "jti": "expired-test",
        },
        get_settings().jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer " + token}).status_code == 401
    with Session(get_engine()) as db:
        db.get(User, user["id"]).active = False
        db.commit()
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_no_eligible_slots_and_cross_request_candidate(client):
    learner, lh, teacher, th, root, child, request = setup_exchange(client)
    path = "/api/v1/requests/" + request["id"]
    candidate = client.post(path + "/matches", headers=lh).json()["candidates"][0]
    payload = {
        key: request[key]
        for key in ["skill_id", "duration_minutes", "window_start", "window_end", "mode"]
    }
    other = client.post("/api/v1/requests", headers=lh, json=payload).json()
    assert (
        client.post(
            "/api/v1/requests/" + other["id"] + "/select",
            headers=lh,
            json={"candidate_id": candidate["id"]},
        ).status_code
        == 422
    )
    with Session(get_engine()) as db:
        for slot in db.scalars(select(Availability).where(Availability.user_id == teacher["id"])):
            db.delete(slot)
        db.commit()
    assert client.post(path + "/matches", headers=lh).json()["candidates"] == []


def test_duration_review_and_request_size_bounds(client, monkeypatch):
    learner, lh, teacher, th, session = booked(client)
    path = "/api/v1/sessions/" + session["id"]
    move_to_end(monkeypatch, session)
    client.post(path + "/start", headers=lh)
    assert client.post(path + "/confirm", headers=lh, json={"minutes": 61}).status_code == 422
    assert client.post(path + "/reviews", headers=lh, json={"stars": 0}).status_code == 422
    assert client.post(path + "/reviews", headers=lh, json={"stars": 6}).status_code == 422
    headers = {**lh, "Origin": "http://localhost:5173"}
    oversized = client.post("/api/v1/requests", headers=headers, content=b"x" * 65537)
    assert oversized.status_code == 413
    assert oversized.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert oversized.json()["error"]["request_id"]
