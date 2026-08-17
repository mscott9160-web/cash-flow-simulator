import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_path: str = "cashflow.db"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    auth_secret: str = "local-development-auth-secret-32-bytes"
    environment: str = "development"

    @classmethod
    def from_environment(cls) -> "Settings":
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
        return cls(database_path=database_path, cors_origins=cors_origins, auth_secret=auth_secret, environment=environment)