"""
Rate Limiting Retry Mechanism Tests for M-flow.

Unit tests for the sleep-and-retry decorators that handle
rate limit errors with exponential backoff.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

import pytest

from m_flow.llm.backends.litellm_instructor.llm.rate_limiter import (
    is_rate_limit_error,
    sleep_and_retry_async,
    sleep_and_retry_sync,
)
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger()

# ============================================================================
# Test Constants
# ============================================================================

RETRY_CONFIG = {
    "max_retries": 3,
    "initial_backoff": 0.1,
    "backoff_factor": 2.0,
}

FAILURES_BEFORE_SUCCESS = 2
MIN_EXPECTED_BACKOFF_TIME = 0.3


# ============================================================================
# Helper Functions (Not Tests)
# ============================================================================


@sleep_and_retry_sync(**RETRY_CONFIG)
def _sync_function_with_retries():
    """Sync function that fails twice, then succeeds."""
    if not hasattr(_sync_function_with_retries, "call_count"):
        _sync_function_with_retries.call_count = 0

    _sync_function_with_retries.call_count += 1
    current = _sync_function_with_retries.call_count

    if current <= FAILURES_BEFORE_SUCCESS:
        logger.info(f"Sync attempt {current}: simulating rate limit")
        raise Exception("429 Too Many Requests: Rate limit exceeded")

    logger.info(f"Sync attempt {current}: success")
    return f"Completed on attempt {current}"


@sleep_and_retry_async(**RETRY_CONFIG)
async def _async_function_with_retries():
    """Async function that fails twice, then succeeds."""
    if not hasattr(_async_function_with_retries, "call_count"):
        _async_function_with_retries.call_count = 0

    _async_function_with_retries.call_count += 1
    current = _async_function_with_retries.call_count

    if current <= FAILURES_BEFORE_SUCCESS:
        logger.info(f"Async attempt {current}: simulating rate limit")
        raise Exception("429 Too Many Requests: Rate limit exceeded")

    logger.info(f"Async attempt {current}: success")
    return f"Completed on attempt {current}"


def reset_function_counters() -> None:
    """Clear call counters on test functions."""
    for fn in [_sync_function_with_retries, _async_function_with_retries]:
        if hasattr(fn, "call_count"):
            delattr(fn, "call_count")


# ============================================================================
# Rate Limit Detection Tests
# ============================================================================


class TestRateLimitDetection:
    """Tests for is_rate_limit_error function."""

    def test_detects_rate_limit_messages(self) -> None:
        """Verify rate limit error patterns are recognized."""
        rate_limit_messages = [
            "429 Rate limit exceeded",
            "Too many requests",
            "rate_limit_exceeded",
            "ratelimit error",
            "You have exceeded your quota",
            "capacity has been exceeded",
            "Service throttled",
        ]

        for msg in rate_limit_messages:
            err = Exception(msg)
            assert is_rate_limit_error(err), f"Should detect: {msg}"
            print(f"✓ Detected: {msg}")

    def test_ignores_non_rate_limit_errors(self) -> None:
        """Verify non-rate-limit errors are not misidentified."""
        other_errors = [
            "404 Not Found",
            "500 Internal Server Error",
            "Invalid API Key",
            "Bad Request",
        ]

        for msg in other_errors:
            err = Exception(msg)
            assert not is_rate_limit_error(err), f"Should not detect: {msg}"
            print(f"✓ Ignored: {msg}")


# ============================================================================
# Sync Retry Tests
# ============================================================================


class TestSyncRetry:
    """Tests for synchronous retry decorator."""

    def test_retries_on_rate_limit(self) -> None:
        """Verify sync decorator retries and succeeds."""
        reset_function_counters()

        start = time.time()
        result = _sync_function_with_retries()
        elapsed = time.time() - start

        attempts = _sync_function_with_retries.call_count

        assert attempts == 3, f"Expected 3 attempts, got {attempts}"
        assert elapsed >= MIN_EXPECTED_BACKOFF_TIME, (
            f"Expected backoff >= {MIN_EXPECTED_BACKOFF_TIME}s, got {elapsed:.2f}s"
        )
        assert "attempt 3" in result, f"Unexpected result: {result}"
        print(f"✓ Sync retry passed: {attempts} attempts, {elapsed:.2f}s")


# ============================================================================
# Async Retry Tests
# ============================================================================


class TestAsyncRetry:
    """Tests for asynchronous retry decorator."""

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit(self) -> None:
        """Verify async decorator retries and succeeds."""
        reset_function_counters()

        start = time.time()
        result = await _async_function_with_retries()
        elapsed = time.time() - start

        attempts = _async_function_with_retries.call_count

        assert attempts == 3, f"Expected 3 attempts, got {attempts}"
        assert elapsed >= MIN_EXPECTED_BACKOFF_TIME, (
            f"Expected backoff >= {MIN_EXPECTED_BACKOFF_TIME}s, got {elapsed:.2f}s"
        )
        assert "attempt 3" in result, f"Unexpected result: {result}"
        print(f"✓ Async retry passed: {attempts} attempts, {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        """Verify exception is raised when max retries exceeded."""

        @sleep_and_retry_async(max_retries=2, initial_backoff=0.1)
        async def always_fails():
            raise Exception("429 Too Many Requests: always failing")

        with pytest.raises(Exception) as exc_info:
            await always_fails()

        assert "always failing" in str(exc_info.value)
        print("✓ Max retries exceeded raises exception")


# ============================================================================
# Main Entry Point
# ============================================================================


async def run_all_tests() -> None:
    """Execute all retry tests."""
    print("\n=== Rate Limit Detection ===")
    detection_tests = TestRateLimitDetection()
    detection_tests.test_detects_rate_limit_messages()
    detection_tests.test_ignores_non_rate_limit_errors()

    print("\n=== Sync Retry ===")
    sync_tests = TestSyncRetry()
    sync_tests.test_retries_on_rate_limit()

    print("\n=== Async Retry ===")
    async_tests = TestAsyncRetry()
    await async_tests.test_retries_on_rate_limit()
    await async_tests.test_raises_after_max_retries()

    print("\n=== All Rate Limiting Tests Passed ===")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_all_tests())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
