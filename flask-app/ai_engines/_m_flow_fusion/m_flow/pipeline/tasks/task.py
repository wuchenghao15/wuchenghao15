"""
Unified task abstraction for the M-Flow pipeline.

A :class:`Task` wraps any callable — sync function, coroutine, generator,
or async generator — and exposes a uniform ``async for`` interface that
emits results grouped into configurable batches.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator
from typing import Any, Dict, Optional


class Stage:
    """
    Normalises arbitrary callables into a single async-iterable contract.

    Parameters
    ----------
    fn : callable
        The work unit to wrap (sync, async, generator, or async generator).
    *defaults
        Positional arguments prepended to every invocation of *fn*.
    config : dict, optional
        Execution hints.  Currently recognised key: ``batch_size`` (default 1).
    task_config : dict, optional
        Alias for *config* (kept for backward compatibility with caller code).
    **kw_defaults
        Keyword arguments merged into every invocation of *fn*.
    """

    __slots__ = ("_fn", "_defaults", "_kw", "_cfg", "_kind", "_batch")

    def __init__(
        self,
        fn: Any,
        *defaults: Any,
        config: Optional[Dict[str, Any]] = None,
        task_config: Optional[Dict[str, Any]] = None,
        **kw_defaults: Any,
    ) -> None:
        if not callable(fn):
            raise TypeError(f"Expected a callable, got {type(fn).__name__}: {fn!r}")

        self._fn = fn
        self._defaults = defaults
        self._kw = kw_defaults
        self._cfg: Dict[str, Any] = {"batch_size": 1, **(config or task_config or {})}
        self._batch: int = self._cfg.get("batch_size", 1)

        match True:
            case _ if inspect.isasyncgenfunction(fn):
                self._kind = "async_gen"
            case _ if inspect.isgeneratorfunction(fn):
                self._kind = "sync_gen"
            case _ if inspect.iscoroutinefunction(fn):
                self._kind = "coroutine"
            case _:
                self._kind = "plain"

    # -- introspection --------------------------------------------------------

    @property
    def executable(self) -> Any:
        """The original unwrapped callable."""
        return self._fn

    @property
    def task_type(self) -> str:
        """Human-readable label for the callable flavour."""
        return {
            "async_gen": "Async Generator",
            "sync_gen": "Generator",
            "coroutine": "Coroutine",
            "plain": "Function",
        }.get(self._kind, "Unknown")

    @property
    def task_config(self) -> Dict[str, Any]:
        return self._cfg

    @property
    def default_params(self) -> Dict[str, Any]:
        return {"args": self._defaults, "kwargs": self._kw}

    # -- invocation -----------------------------------------------------------

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Call the wrapped function with merged default + caller arguments."""
        return self._fn(*(args + self._defaults), **{**self._kw, **kwargs})

    async def execute(
        self,
        inputs: Any,
        next_batch_size: Optional[int] = None,
    ) -> AsyncIterator[Any]:
        """
        Asynchronously iterate over results, yielding lists of *batch_size*.

        Parameters
        ----------
        inputs
            Positional args forwarded to :meth:`run` (unpacked as ``*inputs``).
        next_batch_size
            Override the configured batch size for this single execution.
        """
        effective_batch = next_batch_size if next_batch_size is not None else self._cfg.get("batch_size", 1)

        match self._kind:
            case "async_gen":
                async for chunk in self._collect_async_gen(inputs, effective_batch):
                    yield chunk
            case "sync_gen":
                async for chunk in self._collect_sync_gen(inputs, effective_batch):
                    yield chunk
            case "coroutine":
                yield await self.run(*inputs)
            case _:
                yield self.run(*inputs)

    # -- private collectors ---------------------------------------------------

    async def _collect_async_gen(
        self,
        inputs: Any,
        size: int,
    ) -> AsyncIterator[list]:
        buf: list = []
        async for item in self.run(*inputs):
            buf.append(item)
            if len(buf) >= size:
                yield buf
                buf = []
        if buf:
            yield buf

    async def _collect_sync_gen(
        self,
        inputs: Any,
        size: int,
    ) -> AsyncIterator[list]:
        buf: list = []
        for item in self.run(*inputs):
            buf.append(item)
            if len(buf) >= size:
                yield buf
                buf = []
        if buf:
            yield buf
