"""
Protocol for ingestion data sources.
"""

from __future__ import annotations

from typing import Any, BinaryIO, Protocol, Union


class IngestionData(Protocol):
    """
    Abstract interface for data that can be ingested.
    """

    data: Union[str, BinaryIO]

    def get_data(self) -> Any:
        """Return the raw data content."""
        raise NotImplementedError

    def get_identifier(self) -> str:
        """Return a unique identifier for this data."""
        raise NotImplementedError

    def get_metadata(self) -> dict:
        """Return metadata dictionary for this data."""
        raise NotImplementedError
