import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_path: str = "cashflow.db"
    database_url: str | None = None
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    auth_secret: str = "local-development-auth-secret-32-bytes"
    environment: str = "development"
    auth_rate_limit_max_attempts: int = 10
    auth_rate_limit_window_seconds: int = 900

    @classmethod
    def from_environment(cls) -> "Settings":
        raw_database_url = os.getenv("DATABASE_URL", "").strip()
        database_path = os.getenv("DATABASE_PATH", cls.database_path).strip() or cls.database_path
        raw_origins = os.getenv("CORS_ORIGINS", ",".join(cls.cors_origins))
        cors_origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
        if "*" in cors_origins:
            raise ValueError("CORS_ORIGINS must contain explicit origins")
        environment = os.getenv("ENVIRONMENT", cls.environment).strip().lower() or cls.environment
        auth_secret = os.getenv("AUTH_SECRET", "").strip()
        if not auth_secret:
            if environment in {"production", "prod"}:
                raise ValueError("AUTH_SECRET is required in production")
            auth_secret = cls.auth_secret
        try:
            auth_rate_limit_max_attempts = int(os.getenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", str(cls.auth_rate_limit_max_attempts)))
            auth_rate_limit_window_seconds = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", str(cls.auth_rate_limit_window_seconds)))
        except ValueError as error:
            raise ValueError("AUTH_RATE_LIMIT_MAX_ATTEMPTS and AUTH_RATE_LIMIT_WINDOW_SECONDS must be integers") from error
        if auth_rate_limit_max_attempts < 1 or auth_rate_limit_window_seconds < 1:
            raise ValueError("AUTH_RATE_LIMIT_MAX_ATTEMPTS and AUTH_RATE_LIMIT_WINDOW_SECONDS must be positive")
        return cls(database_path=database_path, database_url=raw_database_url or None, cors_origins=cors_origins, auth_secret=auth_secret, environment=environment, auth_rate_limit_max_attempts=auth_rate_limit_max_attempts, auth_rate_limit_window_seconds=auth_rate_limit_window_seconds)