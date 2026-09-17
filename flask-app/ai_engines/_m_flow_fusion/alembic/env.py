"""M-Flow Alembic environment — async-first migration runner."""

from __future__ import annotations

import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from m_flow.adapters.relational import Base, get_db_adapter

_log = logging.getLogger("alembic.env")


def _bootstrap() -> None:
    """Resolve DSN, configure Alembic, and dispatch migrations."""
    cfg = context.config
    if cfg.config_file_name:
        fileConfig(cfg.config_file_name)

    db = get_db_adapter()
    _log.info("Database: %s", db.db_uri)
    cfg.set_section_option(cfg.config_ini_section, "SQLALCHEMY_DATABASE_URI", db.db_uri)

    meta = Base.metadata

    if context.is_offline_mode():
        _log.info("Offline mode — emitting SQL to stdout")
        context.configure(
            url=cfg.get_main_option("sqlalchemy.url"),
            target_metadata=meta,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
    else:
        asyncio.run(_run_online(cfg, meta))


async def _run_online(cfg, meta) -> None:
    engine = async_engine_from_config(
        cfg.get_section(cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with engine.connect() as conn:
        await conn.run_sync(
            lambda c: _apply(c, meta),
        )
    await engine.dispose()


def _apply(conn, meta) -> None:
    context.configure(connection=conn, target_metadata=meta)
    with context.begin_transaction():
        context.run_migrations()


_bootstrap()
