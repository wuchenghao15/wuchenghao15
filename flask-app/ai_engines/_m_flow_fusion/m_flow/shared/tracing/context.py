# m_flow/shared/tracing/context.py
"""
P6-1: Trace Context

Use contextvars to store current trace, enabling implicit propagation to all async tasks.
"""

from __future__ import annotations
import contextvars
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import TraceState

_current_trace: contextvars.ContextVar[Optional["TraceState"]] = contextvars.ContextVar(
    "m_flow_current_trace", default=None
)


def set_current_trace(trace: Optional["TraceState"]) -> None:
    """Set current trace to context."""
    _current_trace.set(trace)


def get_current_trace() -> Optional["TraceState"]:
    """Get current trace (may be None)."""
    return _current_trace.get()


def clear_current_trace() -> None:
    """Clear current trace."""
    _current_trace.set(None)
