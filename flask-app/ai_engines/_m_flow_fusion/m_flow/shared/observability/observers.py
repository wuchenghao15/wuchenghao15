"""
Observability backend definitions for M-flow.

This module provides an enumeration of monitoring and tracing
platforms that M-flow can integrate with for operational visibility.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

# Default observer when none is configured
DEFAULT_OBSERVER: Final[str] = "none"


class Observer(str, Enum):
    """
    Registry of observability tool integrations.

    M-flow supports pluggable observability backends for:
    - Request/response tracing
    - LLM call monitoring
    - Performance metrics collection
    - Error tracking and debugging

    Usage:
        >>> from m_flow.shared.observability.observers import Observer
        >>> observer = Observer.LANGFUSE
        >>> observer.value
        'langfuse'
    """

    # Disable all observability instrumentation
    NONE = "none"

    # Langfuse: Open-source LLM observability
    # https://langfuse.com
    LANGFUSE = "langfuse"

    # LLMLite: Lightweight LLM monitoring
    LLMLITE = "llmlite"

    # LangSmith: LangChain's observability platform
    # https://smith.langchain.com
    LANGSMITH = "langsmith"

    @classmethod
    def from_string(cls, value: str) -> "Observer":
        """
        Convert a string value to an Observer enum.

        Args:
            value: String representation of the observer.

        Returns:
            Matching Observer enum value, or NONE if not found.
        """
        normalized = value.lower().strip()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.NONE

    def is_enabled(self) -> bool:
        """Check if this observer represents an active integration."""
        return self != Observer.NONE
