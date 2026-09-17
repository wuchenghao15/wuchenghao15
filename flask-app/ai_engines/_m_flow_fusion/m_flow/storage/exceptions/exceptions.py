"""Storage-related exceptions."""

from __future__ import annotations

from fastapi import status

from m_flow.exceptions import BadInputError


class InvalidMemoryNodesError(BadInputError):
    """Raised when memory nodes are invalid."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"Invalid memory_nodes: {detail}",
            "InvalidMemoryNodesError",
            status.HTTP_400_BAD_REQUEST,
        )


# Backwards compat alias
InvalidMemoryNodesInAddMemoryNodesError = InvalidMemoryNodesError
