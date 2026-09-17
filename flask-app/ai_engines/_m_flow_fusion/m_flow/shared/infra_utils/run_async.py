"""Offload synchronous callables to an ``asyncio`` thread-pool executor.

This thin wrapper saves callers from the boilerplate of obtaining the
running loop, building a :class:`functools.partial`, and handling the
``loop`` parameter injection pattern used by some legacy helpers.
"""

from __future__ import annotations

import asyncio
import inspect
from concurrent.futures import Executor
from functools import partial
from typing import Any, Callable, Optional, TypeVar

_R = TypeVar("_R")


def _resolve_loop() -> asyncio.AbstractEventLoop:
    """Return the running loop, falling back to the default loop."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.get_event_loop()


def _needs_loop_arg(fn: Callable[..., Any]) -> bool:
    """Check whether *fn* declares a parameter named ``loop``."""
    return "loop" in inspect.signature(fn).parameters


async def run_async(
    func: Callable[..., _R],
    *positional: Any,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    executor: Optional[Executor] = None,
    **kw: Any,
) -> _R:
    """Schedule *func* in *executor* and return its result asynchronously.

    When *func*'s signature contains a ``loop`` keyword argument the
    current event loop is forwarded automatically — this keeps backwards
    compatibility with older helpers that expected it.
    """
    ev_loop = loop if loop is not None else _resolve_loop()

    if _needs_loop_arg(func):
        bound = partial(func, *positional, loop=ev_loop, **kw)
    else:
        bound = partial(func, *positional, **kw)

    return await ev_loop.run_in_executor(executor, bound)
