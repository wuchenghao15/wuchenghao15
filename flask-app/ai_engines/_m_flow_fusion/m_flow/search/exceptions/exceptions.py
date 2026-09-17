"""Search-related exceptions."""

from __future__ import annotations

from fastapi import status

from m_flow.exceptions import BadInputError


class UnsupportedRecallModeError(BadInputError):
    """Raised when an unsupported recall mode is requested."""

    def __init__(
        self,
        mode: str,
        name: str = "UnsupportedRecallModeError",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(f"Unsupported search type: {mode}", name, status_code)
