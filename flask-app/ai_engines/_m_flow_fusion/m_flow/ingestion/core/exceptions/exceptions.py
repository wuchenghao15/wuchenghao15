"""
Ingestion-specific exceptions.
"""

from __future__ import annotations

from fastapi import status

from m_flow.exceptions import BadInputError


class IngestionError(BadInputError):
    """Raised when ingestion encounters unsupported data types."""

    def __init__(
        self,
        message: str = "Unsupported data type for ingestion.",
        name: str = "IngestionError",
        code: int = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    ) -> None:
        super().__init__(message, name, code)
