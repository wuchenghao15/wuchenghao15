"""Summarization exceptions."""

from __future__ import annotations

from fastapi import status

from m_flow.exceptions import BadInputError


class InvalidSummaryInputsError(BadInputError):
    """Raised when summarization inputs are invalid."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"Invalid compress_text inputs: {detail}",
            "InvalidSummaryInputsError",
            status.HTTP_400_BAD_REQUEST,
        )
