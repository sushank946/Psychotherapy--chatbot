import importlib.util

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    if importlib.util.find_spec("flask") is None:
        pytest.skip("Flask dependency not available in test environment.")

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    import app as app_module

    importlib.reload(app_module)
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def signup(client, username="testuser", email="test@example.com", password="password123"):
    return client.post(
        "/signup",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )


def login(client, username="testuser", password="password123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_signup_login_and_chat_invalid_payload(client):
    signup_response = signup(client)
    assert signup_response.status_code == 200

    login_response = login(client)
    assert login_response.status_code == 200

    response = client.post("/chat", data="not-json")
    assert response.status_code == 415


def test_mood_checkin_and_journal_flow(client):
    signup(client, username="journaler", email="journal@example.com")
    login(client, username="journaler")

    checkin_response = client.post("/checkin", json={"mood": 4, "note": "steady"})
    assert checkin_response.status_code == 200
    assert checkin_response.get_json()["status"] == "saved"

    journal_create = client.post(
        "/journal",
        json={"title": "Day log", "content": "Feeling better today."},
    )
    assert journal_create.status_code == 200
    assert journal_create.get_json()["status"] == "saved"

    journal_list = client.get("/journal")
    assert journal_list.status_code == 200
    data = journal_list.get_json()
    assert "entries" in data
    assert len(data["entries"]) == 1
    assert data["entries"][0]["title"] == "Day log"
