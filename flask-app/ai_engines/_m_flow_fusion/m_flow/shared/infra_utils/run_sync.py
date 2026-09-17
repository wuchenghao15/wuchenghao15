"""
Synchronous execution of async coroutines.

Provides utilities to run async code from synchronous contexts
by spawning background threads with their own event loops.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine, Optional, TypeVar

T = TypeVar("T")


class _ExecutionResult:
    """Container for coroutine execution result or error."""

    def __init__(self) -> None:
        self.value: Any = None
        self.error: Optional[BaseException] = None
        self.completed = False


def _execute_in_thread(
    coro: Coroutine[Any, Any, T],
    result: _ExecutionResult,
    loop: Optional[asyncio.AbstractEventLoop],
    timeout: Optional[float],
) -> None:
    """Thread worker that executes the coroutine."""
    try:
        if loop is not None:
            # Submit to existing loop
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            result.value = future.result(timeout=timeout)
        else:
            # Try to get running loop, fall back to new one
            try:
                current = asyncio.get_running_loop()
                future = asyncio.run_coroutine_threadsafe(coro, current)
                result.value = future.result(timeout=timeout)
            except RuntimeError:
                # No loop running - create one
                result.value = asyncio.run(coro)
        result.completed = True
    except BaseException as err:
        result.error = err
        result.completed = True


def run_sync(
    coro: Coroutine[Any, Any, T],
    running_loop: Optional[asyncio.AbstractEventLoop] = None,
    timeout: Optional[float] = None,
) -> T:
    """
    Execute an async coroutine synchronously.

    Spawns a daemon thread to run the coroutine, allowing
    synchronous code to await async operations.

    Args:
        coro: The coroutine to execute.
        running_loop: Optional event loop to use.
        timeout: Maximum seconds to wait.

    Returns:
        The coroutine's return value.

    Raises:
        asyncio.TimeoutError: If execution exceeds timeout.
        Exception: Any exception raised by the coroutine.
    """
    result = _ExecutionResult()

    worker = threading.Thread(
        target=_execute_in_thread,
        args=(coro, result, running_loop, timeout),
        daemon=True,
    )
    worker.start()
    worker.join(timeout=timeout)

    if worker.is_alive():
        raise asyncio.TimeoutError(f"Coroutine execution exceeded {timeout}s timeout")

    if result.error is not None:
        raise result.error

    return result.value
