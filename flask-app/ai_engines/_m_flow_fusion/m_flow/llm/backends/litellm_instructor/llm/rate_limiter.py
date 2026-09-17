"""
Rate limiter for LLM API calls in M-flow.

Provides configurable rate limiting with automatic retry using
exponential backoff to prevent exceeding provider limits.

Configuration via LLMConfig:
  - llm_rate_limit_enabled: Enable/disable (default: False)
  - llm_rate_limit_requests: Max requests per interval (default: 60)
  - llm_rate_limit_interval: Interval in seconds (default: 60)
"""

from __future__ import annotations

import asyncio
import random
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from limits import RateLimitItemPerMinute, storage
from limits.strategies import MovingWindowRateLimiter

from m_flow.llm.config import get_llm_config
from m_flow.shared.logging_utils import get_logger

_log = get_logger()

F = TypeVar("F", bound=Callable[..., Any])

# Patterns indicating rate limit errors (case-insensitive)
_RATE_LIMIT_PATTERNS = frozenset(
    [
        "rate limit",
        "rate_limit",
        "ratelimit",
        "too many requests",
        "retry after",
        "capacity",
        "quota",
        "limit exceeded",
        "throttled",
        "throttling",
        "exceeded your current quota",
    ]
)

# Retry defaults
_MAX_RETRIES = 5
_INITIAL_BACKOFF = 1.0
_BACKOFF_FACTOR = 2.0
_JITTER = 0.1


class LLMRateLimiter:
    """
    Singleton rate limiter for LLM API calls.

    Uses moving window strategy with configurable limits.
    """

    _instance: "LLMRateLimiter | None" = None

    def __new__(cls) -> "LLMRateLimiter":
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._instance._setup()
        return cls._instance

    def _setup(self) -> None:
        """Initialize limiter from config."""
        cfg = get_llm_config()
        self._enabled = cfg.llm_rate_limit_enabled
        self._requests = cfg.llm_rate_limit_requests
        self._interval = cfg.llm_rate_limit_interval

        self._store = storage.MemoryStorage()
        self._limiter = MovingWindowRateLimiter(self._store)

        # Normalize to per-minute rate
        self._rpm = int(self._requests * 60 / self._interval)

        if self._enabled:
            _log.info(f"Rate limiter: {self._requests} req / {self._interval}s")

    def check_and_hit(self) -> bool:
        """
        Record request and check if allowed.

        Returns:
            True if request is permitted, False if blocked.
        """
        if not self._enabled:
            return True

        limit = RateLimitItemPerMinute(self._rpm)
        return self._limiter.hit(limit, "llm_api")

    def wait_sync(self) -> float:
        """
        Block until request is allowed.

        Returns:
            Seconds waited.
        """
        if not self._enabled:
            return 0.0

        total = 0.0
        while not self.check_and_hit():
            time.sleep(0.5)
            total += 0.5
        return total

    async def wait_async(self) -> float:
        """
        Async wait until request is allowed.

        Returns:
            Seconds waited.
        """
        if not self._enabled:
            return 0.0

        total = 0.0
        while not self.check_and_hit():
            await asyncio.sleep(0.5)
            total += 0.5
        return total


# Singleton accessor
llm_rate_limiter = LLMRateLimiter


def _is_rate_limit_error(err: Exception) -> bool:
    """Check if exception indicates rate limiting."""
    msg = str(err).lower()
    return any(p in msg for p in _RATE_LIMIT_PATTERNS)


def _calc_backoff(
    attempt: int,
    initial: float = _INITIAL_BACKOFF,
    factor: float = _BACKOFF_FACTOR,
    jitter: float = _JITTER,
) -> float:
    """Calculate exponential backoff with jitter."""
    base = initial * (factor**attempt)
    delta = base * jitter
    return base + random.uniform(-delta, delta)


def rate_limit_sync(func: F) -> F:
    """Decorator to apply sync rate limiting."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        limiter = LLMRateLimiter()
        waited = limiter.wait_sync()
        if waited > 0:
            _log.debug(f"Rate limited: waited {waited:.1f}s")
        return func(*args, **kwargs)

    return wrapper  # type: ignore


def rate_limit_async(func: F) -> F:
    """Decorator to apply async rate limiting."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        limiter = LLMRateLimiter()
        waited = await limiter.wait_async()
        if waited > 0:
            _log.debug(f"Rate limited: waited {waited:.1f}s")
        return await func(*args, **kwargs)

    return wrapper  # type: ignore


def sleep_and_retry_sync(
    max_retries: int = _MAX_RETRIES,
    initial_backoff: float = _INITIAL_BACKOFF,
    backoff_factor: float = _BACKOFF_FACTOR,
    jitter: float = _JITTER,
) -> Callable[[F], F]:
    """
    Decorator for sync functions with auto-retry on rate limits.

    Uses exponential backoff with jitter.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if not _is_rate_limit_error(e) or attempt > max_retries:
                        raise

                    delay = _calc_backoff(attempt, initial_backoff, backoff_factor, jitter)
                    _log.warning(f"Rate limit retry {attempt}/{max_retries}, waiting {delay:.1f}s: {e}")
                    time.sleep(delay)

        return wrapper  # type: ignore

    return decorator


def sleep_and_retry_async(
    max_retries: int = _MAX_RETRIES,
    initial_backoff: float = _INITIAL_BACKOFF,
    backoff_factor: float = _BACKOFF_FACTOR,
    jitter: float = _JITTER,
) -> Callable[[F], F]:
    """
    Decorator for async functions with auto-retry on rate limits.

    Uses exponential backoff with jitter.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if not _is_rate_limit_error(e) or attempt > max_retries:
                        raise

                    delay = _calc_backoff(attempt, initial_backoff, backoff_factor, jitter)
                    _log.warning(f"Rate limit retry {attempt}/{max_retries}, waiting {delay:.1f}s: {e}")
                    await asyncio.sleep(delay)

        return wrapper  # type: ignore

    return decorator


# Compatibility aliases
is_rate_limit_error = _is_rate_limit_error
calculate_backoff = _calc_backoff
