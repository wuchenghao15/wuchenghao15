"""
Database-aware concurrency control for pipeline operations.

Provides intelligent concurrency management based on the underlying
database backend. SQLite requires serial writes due to file-level
locking, while PostgreSQL supports high concurrency.

Environment Variables
---------------------
MFLOW_PIPELINE_CONCURRENCY : int
    Override automatic concurrency detection.
    - 0 or unset: Auto-detect based on database type
    - 1: Force serial execution (safe for any database)
    - N > 1: Allow N concurrent operations (use with caution on SQLite)
"""

from __future__ import annotations

import asyncio
import os
from functools import lru_cache
from typing import Any, Coroutine, List, TypeVar

from m_flow.shared.logging_utils import get_logger

logger = get_logger("db_concurrency")

T = TypeVar("T")


@lru_cache(maxsize=1)
def _detect_db_provider() -> str:
    """
    Detect the configured database provider.

    Returns
    -------
    str
        Database provider name ('sqlite' or 'postgresql').
    """
    # Import here to avoid circular imports
    from m_flow.adapters.relational.config import get_relational_config

    config = get_relational_config()
    return config.db_provider.lower()


def _compute_concurrency_limit() -> int:
    """
    Compute concurrency limit (internal, uncached).

    This is separated from get_pipeline_concurrency_limit to allow
    logging to happen only once while still using lru_cache.
    """
    # Check for explicit override
    override = os.getenv("MFLOW_PIPELINE_CONCURRENCY", "").strip()
    if override and override.isdigit():
        limit = int(override)
        if limit > 0:
            return limit

    # Auto-detect based on database type
    provider = _detect_db_provider()

    if provider == "sqlite":
        return 1
    elif provider in ("postgres", "postgresql"):
        return 20
    else:
        return 1


# Flag to track if we've logged the concurrency setting
_concurrency_logged = False


@lru_cache(maxsize=1)
def get_pipeline_concurrency_limit() -> int:
    """
    Get the concurrency limit for pipeline batch processing.

    Automatically detects database type and sets appropriate limits:
    - SQLite: 1 (serial execution to avoid database locks)
    - PostgreSQL: 20 (high concurrency)

    Can be overridden via MFLOW_PIPELINE_CONCURRENCY environment variable.

    Returns
    -------
    int
        Maximum concurrent operations allowed.
    """
    global _concurrency_logged

    limit = _compute_concurrency_limit()

    # Log only once
    if not _concurrency_logged:
        _concurrency_logged = True

        override = os.getenv("MFLOW_PIPELINE_CONCURRENCY", "").strip()
        if override and override.isdigit() and int(override) > 0:
            logger.info(f"[db_concurrency] Using override concurrency limit: {limit}")
        else:
            provider = _detect_db_provider()
            if provider == "sqlite":
                logger.info(
                    "[db_concurrency] SQLite detected - using serial execution (concurrency=1) "
                    "to avoid 'database is locked' errors"
                )
            elif provider in ("postgres", "postgresql"):
                logger.info(f"[db_concurrency] PostgreSQL detected - using high concurrency (limit={limit})")
            else:
                logger.warning(
                    f"[db_concurrency] Unknown database provider '{provider}' - "
                    f"defaulting to serial execution for safety"
                )

    return limit


async def run_with_concurrency_limit(
    coros: List[Coroutine[Any, Any, T]],
    concurrency_limit: int | None = None,
) -> List[T]:
    """
    Execute coroutines with database-aware concurrency control.

    For SQLite, executes serially to avoid lock conflicts.
    For PostgreSQL, executes in parallel up to the concurrency limit.

    Parameters
    ----------
    coros : List[Coroutine]
        Coroutines to execute.
    concurrency_limit : int | None
        Override the auto-detected limit. If None, uses get_pipeline_concurrency_limit().

    Returns
    -------
    List[T]
        Results from all coroutines, in order.

    Example
    -------
    >>> results = await run_with_concurrency_limit([
    ...     process_item(item) for item in items
    ... ])
    """
    if not coros:
        return []

    limit = concurrency_limit if concurrency_limit is not None else get_pipeline_concurrency_limit()

    if limit == 1:
        # Serial execution for SQLite
        results = []
        for coro in coros:
            result = await coro
            results.append(result)
        return results

    elif limit >= len(coros):
        # Full parallel execution
        return await asyncio.gather(*coros)

    else:
        # Semaphore-limited parallel execution
        semaphore = asyncio.Semaphore(limit)

        async def limited_coro(coro: Coroutine) -> T:
            async with semaphore:
                return await coro

        return await asyncio.gather(*[limited_coro(c) for c in coros])


def is_sqlite_mode() -> bool:
    """
    Check if currently using SQLite database.

    Returns
    -------
    bool
        True if SQLite is the configured database provider.
    """
    return _detect_db_provider() == "sqlite"


def clear_concurrency_cache() -> None:
    """
    Clear cached concurrency settings.

    Useful for testing or when database configuration changes.
    """
    global _concurrency_logged
    _concurrency_logged = False
    _detect_db_provider.cache_clear()
    get_pipeline_concurrency_limit.cache_clear()
