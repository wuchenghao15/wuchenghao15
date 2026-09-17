"""
Binary data wrapper for ingestion.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, BinaryIO, Dict, Optional

from m_flow.shared.files import FileMetadata, get_file_metadata
from m_flow.shared.infra_utils.run_sync import run_sync

from .IngestionData import IngestionData


def create_binary_data(data: BinaryIO, name: Optional[str] = None) -> "BinaryData":
    """Factory function for BinaryData."""
    return BinaryData(data, name)


class BinaryData(IngestionData):
    """
    Wrapper for binary file content.
    """

    def __init__(self, data: BinaryIO, name: Optional[str] = None) -> None:
        self.data = data
        self.name = name
        self._metadata: Optional[FileMetadata] = None

    def get_identifier(self) -> str:
        """Return content hash as identifier."""
        return self.get_metadata()["content_hash"]

    def get_metadata(self) -> Dict[str, Any]:
        """Return file metadata with content hash."""
        run_sync(self._ensure_metadata())
        return self._metadata  # type: ignore

    async def _ensure_metadata(self) -> None:
        """Lazily compute file metadata."""
        if self._metadata is not None:
            return
        self._metadata = await get_file_metadata(self.data, name=self.name)
        if self._metadata.get("name") is None:
            self._metadata["name"] = self.name

    @asynccontextmanager
    async def get_data(self) -> AsyncIterator[BinaryIO]:
        """Yield the binary content."""
        yield self.data
