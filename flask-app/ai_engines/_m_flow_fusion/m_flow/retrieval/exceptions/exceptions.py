"""
Retrieval-specific exception types.
"""

from __future__ import annotations

from fastapi import status

from m_flow.exceptions import InternalError, BadInputError


class UnsupportedRecallMode(BadInputError):
    """Raised when the requested recall mode is not available for the adapter."""

    def __init__(
        self,
        msg: str = "Recall mode not supported by the current adapter.",
        name: str = "UnsupportedRecallMode",
        code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(msg, name, code)


# Backwards compat alias
RecallModeNotSupported = UnsupportedRecallMode


class CypherExecutionError(InternalError):
    """Raised when a Cypher query fails."""

    def __init__(
        self,
        msg: str = "Cypher query execution failed.",
        name: str = "CypherExecutionError",
        code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(msg, name, code)


CypherSearchError = CypherExecutionError


class EmptyDatasetError(BadInputError):
    """Raised when no data exists for the requested operation."""

    def __init__(
        self,
        msg: str = "No data found. Please add data first.",
        name: str = "EmptyDatasetError",
        code: int = status.HTTP_404_NOT_FOUND,
    ) -> None:
        super().__init__(msg, name, code)


NoDataError = EmptyDatasetError


class MissingDistancesError(BadInputError):
    """Raised when collection distance metrics are unavailable."""

    def __init__(
        self,
        msg: str = "Collection distances not found for the query.",
        name: str = "MissingDistancesError",
        code: int = status.HTTP_404_NOT_FOUND,
    ) -> None:
        super().__init__(msg, name, code)


CollectionDistancesNotFoundError = MissingDistancesError
