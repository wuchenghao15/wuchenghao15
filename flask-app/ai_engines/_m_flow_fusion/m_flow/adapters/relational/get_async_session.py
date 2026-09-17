"""
Async database session context manager.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .get_db_adapter import get_db_adapter


@asynccontextmanager
async def get_async_session(
    commit: bool = False,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session.

    Args:
        commit: Whether to auto-commit on successful exit.

    Yields:
        AsyncSession instance.
    """
    db = get_db_adapter()

    async with db.get_async_session() as sess:
        yield sess

        if commit:
            await sess.commit()
