"""
Document base class model.
"""

from __future__ import annotations

from typing import Any, Type

from m_flow.core import MemoryNode
from m_flow.ingestion.chunking.Chunker import Chunker


class Document(MemoryNode):
    """
    Base class for document content processing.

    Attributes:
        name: Document name.
        processed_path: Processed data location.
        external_metadata: External metadata JSON string.
        mime_type: MIME type.
    """

    name: str
    processed_path: str
    external_metadata: str | None = None
    mime_type: str

    metadata: dict = {"index_fields": ["name"]}

    async def read(
        self,
        chunker_cls: Type[Chunker],
        max_chunk_size: int,
    ) -> Any:
        """
        Read and chunk document content.

        Subclasses must override this method to implement specific read logic.
        """
        raise NotImplementedError("Subclasses must implement read method")
