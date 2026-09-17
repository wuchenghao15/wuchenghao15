"""
Observability decorator factory.

Provides a function to retrieve the appropriate observability decorator
based on the configured monitoring tool.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from m_flow.base_config import get_base_config

from .observers import Observer

F = TypeVar("F", bound=Callable[..., Any])


def _create_noop_decorator() -> Callable[..., Any]:
    """
    Create a no-op decorator that accepts any arguments.

    Handles both direct decoration (@observe) and parameterized
    decoration (@observe(as_type="generation")).
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Direct decoration case: @observe on a function
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]

        # Parameterized decoration case: @observe(...)
        def passthrough(fn: F) -> F:
            return fn

        return passthrough

    return wrapper


def get_observe() -> Callable[..., Any]:
    """
    Get the observability decorator based on configuration.

    Returns the Langfuse observe decorator if configured, otherwise
    returns a no-op decorator that passes functions through unchanged.

    Returns:
        A decorator function for observability instrumentation.
    """
    config = get_base_config()
    tool = config.monitoring_tool

    if tool == Observer.LANGFUSE:
        from langfuse.decorators import observe

        return observe

    # Default: no-op observer
    return _create_noop_decorator()
