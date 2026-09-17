"""
M-flow exception hierarchy.

All user-facing error types are gathered here so callers can
``from m_flow.exceptions import ServiceFault`` without reaching
into internal modules.

Categories
----------
* **Base**:   ``ServiceFault`` → ``InternalError`` / ``BadInputError`` /
              ``ConfigError`` / ``TransientError``
* **Public**: ``ServiceFault`` (generic), ``InternalError``,
              ``BadInputError``, ``ConfigError``,
              ``TransientError``
"""

from __future__ import annotations

from .exceptions import (
    ConfigError,
    InternalError,
    BadInputError,
    ServiceFault,
    TransientError,
)

__all__ = [
    "BadInputError",
    "ConfigError",
    "InternalError",
    "ServiceFault",
    "ConfigError",
    "InternalError",
    "TransientError",
    "BadInputError",
    "ServiceFault",
    "TransientError",
]
