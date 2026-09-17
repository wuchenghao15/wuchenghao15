"""
File operation exceptions for M-flow.

Provides custom exception types for file handling errors,
with HTTP status codes for API layer translation.
"""

from __future__ import annotations

# Status codes
HTTP_UNPROCESSABLE_ENTITY = 422


class FileContentHashingError(Exception):
    """
    Raised when content hash computation fails.

    This error occurs when the system cannot compute a SHA-256
    digest for a file, typically due to I/O issues or
    unsupported stream operations.

    Attributes:
        message: Human-readable error description.
        name: Exception type name for logging.
        status_code: HTTP status code for API responses.

    Example:
        >>> raise FileContentHashingError("Stream does not support seeking")
    """

    def __init__(
        self,
        message: str = "Failed to compute content hash for file",
        *,
        name: str = "FileContentHashingError",
        status_code: int = HTTP_UNPROCESSABLE_ENTITY,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.name = name
        self.status_code = status_code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"
