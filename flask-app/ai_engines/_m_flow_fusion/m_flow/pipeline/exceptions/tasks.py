"""Pipeline task exceptions."""

from __future__ import annotations

from fastapi import status

from m_flow.exceptions import BadInputError


class WrongTaskTypeError(BadInputError):
    """Raised when tasks argument contains invalid types."""

    def __init__(
        self,
        message: str = "tasks must be a list of Stage instances.",
        name: str = "WrongTaskTypeError",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message, name, status_code)
