import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


@pytest.fixture
def client():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated disposable PostgreSQL database")
    # Prevent accidental erasure of a development database by requiring a test name.
    from sqlalchemy.engine import make_url

    assert make_url(url).database.endswith("_test"), "Test database name must end in _test"
    from app.config import get_settings
    from app.database import get_engine

    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    get_engine.cache_clear()
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users, skills RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE auth_attempts"))
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    get_engine().dispose()
    get_engine.cache_clear()
    engine.dispose()


def register(client, name="Learner", email="learner@example.com"):
    payload = {"name": name, "email": email, "password": "Strong-Demo-Password1"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    token = client.post(
        "/api/v1/auth/token", data={"username": email, "password": payload["password"]}
    )
    assert token.status_code == 200, token.text
    return response.json(), {"Authorization": "Bearer " + token.json()["access_token"]}
