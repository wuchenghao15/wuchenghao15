"""Vector adapter exceptions."""

from __future__ import annotations

from fastapi import status

from m_flow.exceptions import BadInputError


class CollectionNotFoundError(BadInputError):
    """Raised when a requested vector collection cannot be found."""

    def __init__(
        self,
        message: str,
        name: str = "CollectionNotFoundError",
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
        log: bool = True,
        log_level: str = "DEBUG",
    ) -> None:
        super().__init__(message, name, status_code, log, log_level)
