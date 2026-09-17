"""
Concrete exception subclasses for the shared utilities layer.

Every exception inherits from ``BadInputError`` and carries an
HTTP-compatible *status_code* so API handlers can surface meaningful
error responses without extra mapping logic.
"""

from __future__ import annotations

from http import HTTPStatus

from m_flow.exceptions import BadInputError


class IngestionError(BadInputError):
    """Raised when a data-ingestion / loading step cannot complete.

    Defaults to HTTP 422 (Unprocessable Content) unless the caller
    provides a different status code.
    """

    _DEFAULT_MSG: str = "Data ingestion failed."
    _DEFAULT_NAME: str = "IngestionError"
    _DEFAULT_CODE: int = HTTPStatus.UNPROCESSABLE_ENTITY.value  # 422

    def __init__(
        self,
        message: str = _DEFAULT_MSG,
        name: str = _DEFAULT_NAME,
        status_code: int = _DEFAULT_CODE,
    ) -> None:
        super().__init__(message, name, status_code)
