"""Error types specific to the infra-data processing layer."""

from __future__ import annotations

from http import HTTPStatus

from m_flow.exceptions import BadInputError


class KeywordExtractionError(BadInputError):
    """The keyword extractor received unusable input (empty or whitespace-only).

    Callers should pre-validate that the incoming text is non-trivial
    before invoking extraction to avoid this error.
    """

    _DEFAULT_MSG = "Keyword extraction failed: the input text was empty or invalid."

    def __init__(
        self,
        message: str | None = None,
        *,
        name: str = "KeywordExtractionError",
        status_code: int = HTTPStatus.BAD_REQUEST,
    ) -> None:
        super().__init__(
            message or self._DEFAULT_MSG,
            name,
            status_code,
        )
