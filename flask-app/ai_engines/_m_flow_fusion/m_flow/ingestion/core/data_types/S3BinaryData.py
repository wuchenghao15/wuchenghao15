"""
S3 binary data wrapper for ingestion.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from m_flow.shared.files import FileMetadata, get_file_metadata
from m_flow.shared.infra_utils import run_sync

from .IngestionData import IngestionData


def create_s3_binary_data(s3_path: str, name: Optional[str] = None) -> "S3BinaryData":
    """Factory function for S3BinaryData."""
    return S3BinaryData(s3_path, name=name)


class S3BinaryData(IngestionData):
    """
    Wrapper for S3-hosted binary content.
    """

    def __init__(self, s3_path: str, name: Optional[str] = None) -> None:
        self.s3_path = s3_path
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
        """Lazily compute file metadata from S3."""
        if self._metadata is not None:
            return

        from m_flow.shared.files.storage.S3FileStorage import S3FileStorage

        dir_path = os.path.dirname(self.s3_path)
        filename = os.path.basename(self.s3_path)

        storage = S3FileStorage(dir_path)
        async with storage.open(filename, "rb") as f:
            self._metadata = await get_file_metadata(f)

        if self._metadata.get("name") is None:
            self._metadata["name"] = self.name or filename

    @asynccontextmanager
    async def get_data(self) -> AsyncIterator[Any]:
        """Yield the binary content from S3."""
        from m_flow.shared.files.storage.S3FileStorage import S3FileStorage

        dir_path = os.path.dirname(self.s3_path)
        filename = os.path.basename(self.s3_path)

        storage = S3FileStorage(dir_path)
        async with storage.open(filename, "rb") as f:
            yield f
