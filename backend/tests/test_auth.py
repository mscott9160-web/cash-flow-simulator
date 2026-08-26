from fastapi.testclient import TestClient
from dataclasses import replace

import backend.api as api
from backend.api import app
from backend.auth import auth_rate_limiter
from backend.storage import ScenarioStore


client = TestClient(app)


def _register(email: str, password: str) -> str:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _reset_auth_rate_limit() -> None:
    auth_rate_limiter.clear()


def test_registration_and_login_return_bearer_token(tmp_path, monkeypatch):
    _reset_auth_rate_limit()
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "auth.sqlite")))

    token = _register("User@Example.com", "correct horse")
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "correct horse"})

    assert len(token) > 20
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["access_token"]


def test_protected_route_rejects_missing_bearer_token(tmp_path, monkeypatch):
    _reset_auth_rate_limit()
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "protected.sqlite")))

    response = client.post("/api/v1/accounts", json={"starting_balance": "0", "as_of": "2025-01-01"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_same_user_can_access_account_and_other_user_gets_not_found(tmp_path, monkeypatch):
    _reset_auth_rate_limit()
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "ownership.sqlite")))
    first_token = _register("first@example.com", "first password")
    second_token = _register("second@example.com", "second password")

    created = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {first_token}"},
        json={"starting_balance": "10", "as_of": "2025-01-01"},
    )
    account_id = created.json()["id"]
    same_user = client.get(f"/api/v1/accounts/{account_id}/projection", headers={"Authorization": f"Bearer {first_token}"})
    other_user = client.get(f"/api/v1/accounts/{account_id}/projection", headers={"Authorization": f"Bearer {second_token}"})

    assert same_user.status_code == 200
    assert other_user.status_code == 404


def test_login_rejects_bad_password_without_exposing_password_data(tmp_path, monkeypatch):
    _reset_auth_rate_limit()
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "bad-password.sqlite")))
    _register("user@example.com", "correct password")

    response = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong password"})

    assert response.status_code == 401
    assert "password_hash" not in response.text
    assert "correct password" not in response.text


def test_auth_rate_limit_applies_per_action_and_ip(tmp_path, monkeypatch):
    _reset_auth_rate_limit()
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "rate-limit.sqlite")))
    monkeypatch.setattr(api, "settings", replace(api.settings, auth_rate_limit_max_attempts=2, auth_rate_limit_window_seconds=60))

    for _ in range(2):
        assert client.post("/api/v1/auth/login", json={"email": "unknown@example.com", "password": "wrong password"}).status_code == 401
    limited = client.post("/api/v1/auth/login", json={"email": "unknown@example.com", "password": "wrong password"})

    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"
    assert client.post("/api/v1/auth/register", json={"email": "new@example.com", "password": "correct password"}).status_code == 200