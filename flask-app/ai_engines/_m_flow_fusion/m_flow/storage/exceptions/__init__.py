"""
Storage layer exceptions.

This module provides custom exception types for storage operations.
All storage-related errors should inherit from these base classes.

Example usage::

    from m_flow.storage.exceptions import InvalidMemoryNodesError

    if not nodes:
        raise InvalidMemoryNodesError("Empty node collection")
"""

from m_flow.storage.exceptions.exceptions import (
    InvalidMemoryNodesError as InvalidMemoryNodesError,
)

# Alias
InvalidMemoryNodesInAddMemoryNodesError = InvalidMemoryNodesError

__all__: list[str] = [
    "InvalidMemoryNodesError",
    "InvalidMemoryNodesInAddMemoryNodesError",
]
