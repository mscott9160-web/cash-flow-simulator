import pytest

from backend.settings import Settings


def test_settings_use_defaults(monkeypatch):
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert Settings.from_environment() == Settings()


def test_settings_parse_database_path_and_origins(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", " /tmp/test.sqlite ")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://app.example.com")

    settings = Settings.from_environment()

    assert settings.database_path == "/tmp/test.sqlite"
    assert settings.cors_origins == ("http://localhost:3000", "https://app.example.com")


def test_settings_reject_wildcard_cors_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(ValueError, match="explicit origins"):
        Settings.from_environment()


def test_settings_require_auth_secret_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("AUTH_SECRET", raising=False)

    with pytest.raises(ValueError, match="AUTH_SECRET"):
        Settings.from_environment()