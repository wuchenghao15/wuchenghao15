"""Neo4j transient-fault retry decorator.

Wraps async graph operations so that deadlocks, transient failures and
temporary unavailability are retried transparently with exponential
back-off computed by the shared ``calculate_backoff`` helper.
"""

from __future__ import annotations

import asyncio
from functools import wraps
from typing import Callable, TypeVar

from m_flow.shared.infra_utils.calculate_backoff import calculate_backoff
from m_flow.shared.logging_utils import get_logger

_retry_log = get_logger("neo4j.deadlock_retry")

_Fn = TypeVar("_Fn", bound=Callable)

_RETRYABLE_MARKERS = frozenset({"DeadlockDetected", "Neo.TransientError"})


def deadlock_retry(max_retries: int = 10) -> Callable[[_Fn], _Fn]:
    """Return a decorator that retries on Neo4j transient errors.

    The decorated coroutine is re-invoked up to *max_retries* times when
    the driver raises a ``Neo4jError`` whose message contains one of the
    known retryable markers, or when a ``DatabaseUnavailable`` exception
    is caught.  Each retry is preceded by an exponentially increasing
    sleep period.

    Parameters
    ----------
    max_retries:
        Upper bound on the number of retry attempts (inclusive).
    """

    def _wrap(fn: _Fn) -> _Fn:
        @wraps(fn)
        async def _inner(self, *args, **kwargs):
            from neo4j.exceptions import DatabaseUnavailable, Neo4jError

            remaining = max_retries

            for current_try in range(1, max_retries + 2):
                try:
                    return await fn(self, *args, **kwargs)

                except Neo4jError as exc:
                    remaining -= 1
                    if remaining < 0:
                        raise

                    exc_repr = str(exc)
                    if not any(tag in exc_repr for tag in _RETRYABLE_MARKERS):
                        raise

                    pause = calculate_backoff(current_try)
                    _retry_log.warning(
                        "Transient Neo4j fault – attempt %d/%d, backing off %.2f s",
                        current_try,
                        max_retries,
                        pause,
                    )
                    await asyncio.sleep(pause)

                except DatabaseUnavailable:
                    remaining -= 1
                    if remaining < 0:
                        raise

                    pause = calculate_backoff(current_try)
                    _retry_log.warning(
                        "Database unavailable – attempt %d/%d, backing off %.2f s",
                        current_try,
                        max_retries,
                        pause,
                    )
                    await asyncio.sleep(pause)

        return _inner  # type: ignore[return-value]

    return _wrap
