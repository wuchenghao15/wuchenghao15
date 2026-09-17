"""Database initialization utility."""

from __future__ import annotations

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from m_flow.shared.logging_utils import get_logger

from .get_db_adapter import get_db_adapter


logger = get_logger(__name__)


async def create_db_and_tables() -> None:
    """Create database schema and tables."""
    engine = get_db_adapter()
    await engine.create_database()

    # Pre-create default permissions to avoid race conditions
    await _ensure_default_permissions_exist()


async def _ensure_default_permissions_exist() -> None:
    """
    Pre-create all known permission types at startup.

    This prevents race conditions when multiple concurrent requests
    try to create the same permission simultaneously.

    Uses the same SAVEPOINT pattern as get_or_create_permission
    for consistency and safety.
    """
    from m_flow.auth.models import Permission
    from m_flow.auth.permissions import PERMISSION_TYPES

    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        for perm_name in PERMISSION_TYPES:
            # Check if permission exists
            existing = await session.execute(select(Permission).where(Permission.name == perm_name))
            if existing.scalars().first() is not None:
                continue

            # Try to create with SAVEPOINT (handles concurrent startup)
            try:
                async with session.begin_nested():
                    await session.execute(insert(Permission).values(name=perm_name))
                logger.info(f"Created permission: {perm_name}")
            except IntegrityError:
                # Another process created it - that's fine
                pass

        await session.commit()

    logger.info(f"Default permissions initialized: {', '.join(PERMISSION_TYPES)}")
