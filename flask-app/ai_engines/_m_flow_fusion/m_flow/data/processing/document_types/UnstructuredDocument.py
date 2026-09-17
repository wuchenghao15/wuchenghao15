"""
Unstructured document processor.

Extracts text from various document formats using unstructured library.
"""

from __future__ import annotations

from io import StringIO
from typing import Any, AsyncGenerator

from m_flow.data.exceptions import UnstructuredLibraryImportError
from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.shared.files.utils.open_data_file import open_data_file

from .Document import Document


class UnstructuredDocument(Document):
    """
    Document type for files processed via unstructured library.

    Supports PDFs, Office documents, images, and other formats
    that require specialized parsing.
    """

    type: str = "unstructured"

    async def read(
        self,
        chunker_cls: Chunker,
        max_chunk_size: int,
    ) -> AsyncGenerator[Any, Any]:
        """
        Extract and chunk document content.

        Uses unstructured library for parsing, then chunks
        extracted text for downstream processing.

        Args:
            chunker_cls: Chunker implementation class.
            max_chunk_size: Maximum tokens per chunk.

        Yields:
            Content fragments.
        """

        async def text_generator():
            try:
                from unstructured.partition.auto import partition
            except ModuleNotFoundError:
                raise UnstructuredLibraryImportError()

            async with open_data_file(self.processed_path, mode="rb") as f:
                parsed = partition(file=f, content_type=self.mime_type)

            # Combine elements into single buffer
            combined = "\n\n".join(str(el) for el in parsed)
            buffer = StringIO(combined)
            buffer.seek(0)

            # Stream in chunks
            while True:
                block = buffer.read(1024)
                if not block.strip():
                    break
                yield block

        chunker = chunker_cls(
            self,
            get_text=text_generator,
            max_chunk_size=max_chunk_size,
        )

        async for fragment in chunker.read():
            yield fragment
