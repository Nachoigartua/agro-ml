"""Alembic environment configuration."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.engine.url import URL

from app.db.base import Base
from app.db import models  # noqa: F401  # Ensure models are imported

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolved_database_url() -> str:
    """Retrieve and normalise database URL from the Alembic config."""

    raw_url = config.get_main_option("sqlalchemy.url")
    url: URL = make_url(raw_url)
    if url.drivername.startswith("postgresql"):
        url = url.set(drivername="postgresql")
    if url.drivername == "sqlite":
        url = url.set(drivername="sqlite")
    resolved = str(url)
    print(f"[alembic] Using database URL: {resolved}", flush=True)
    return resolved


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    context.configure(
        url=_resolved_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _run_sync_migrations(connection: Connection) -> None:
    """Run migrations within a synchronous connection."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""

    from sqlalchemy import create_engine

    connectable = create_engine(
        _resolved_database_url(),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _run_sync_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
