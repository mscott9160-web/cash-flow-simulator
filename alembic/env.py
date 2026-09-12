import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def database_url() -> str:
    configured_url = os.getenv("DATABASE_URL", "").strip()
    if configured_url:
        return configured_url
    configured_path = os.getenv("DATABASE_PATH", "cashflow.db").strip() or "cashflow.db"
    if configured_path.startswith("sqlite:"):
        return configured_path
    if configured_path == ":memory:":
        return "sqlite:///:memory:"
    return f"sqlite:///{Path(configured_path).as_posix()}"


config.set_main_option("sqlalchemy.url", database_url())


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=None, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()