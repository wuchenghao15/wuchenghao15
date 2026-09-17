"""
Text data wrapper for ingestion.
"""

from __future__ import annotations

import hashlib
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from .IngestionData import IngestionData


def create_text_data(data: str) -> "TextData":
    """Factory function for TextData."""
    return TextData(data)


class TextData(IngestionData):
    """
    Wrapper for plain text content.
    """

    def __init__(self, data: str) -> None:
        self.data = data
        self._metadata: Optional[Dict[str, Any]] = None

    def get_identifier(self) -> str:
        """Return content hash as identifier."""
        return self.get_metadata()["content_hash"]

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata with content hash and generated name."""
        self._ensure_metadata()
        return self._metadata  # type: ignore

    def _ensure_metadata(self) -> None:
        """Lazily compute metadata."""
        if self._metadata is not None:
            return
        encoded = self.data.encode("utf-8")
        content_hash = hashlib.md5(encoded).hexdigest()
        self._metadata = {
            "name": f"text_{content_hash}.txt",
            "content_hash": content_hash,
        }

    @asynccontextmanager
    async def get_data(self) -> AsyncIterator[str]:
        """Yield the text content."""
        yield self.data
