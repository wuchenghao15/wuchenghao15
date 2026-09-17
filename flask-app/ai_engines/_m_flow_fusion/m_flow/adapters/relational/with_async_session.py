"""
Async session decorator for database operations.

Provides automatic session management for async database functions.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .get_async_session import get_async_session


def _extract_session(args: tuple) -> Optional[AsyncSession]:
    """Check if last positional arg is a session."""
    if args and isinstance(args[-1], AsyncSession):
        return args[-1]
    return None


def with_async_session(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that provides an async database session.

    If a session is passed via kwargs['session'] or as the last positional
    argument, it will be used. Otherwise, a new session is created and
    committed after the function completes.

    Usage:
        @with_async_session
        async def my_db_operation(data, session=None):
            # session is guaranteed to be available
            ...
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check for existing session
        existing = kwargs.get("session") or _extract_session(args)

        if existing is not None:
            # Use provided session without commit
            return await func(*args, **kwargs)

        # Create new session with auto-commit
        async with get_async_session() as session:
            result = await func(*args, session=session, **kwargs)
            await session.commit()
            return result

    return wrapper
