"""
Plain text document processor.

Handles raw text files with streaming read.
"""

from __future__ import annotations

from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.shared.files.utils.open_data_file import open_data_file

from .Document import Document


class TextDocument(Document):
    """
    Document type for plain text files.

    Streams file content in blocks for chunking.
    """

    type: str = "text"
    mime_type: str = "text/plain"

    async def read(self, chunker_cls: Chunker, max_chunk_size: int):
        """
        Read and chunk text file.

        Args:
            chunker_cls: Chunker implementation.
            max_chunk_size: Token limit per chunk.

        Yields:
            Content fragments from text.
        """

        async def text_generator():
            async with open_data_file(
                self.processed_path,
                mode="r",
                encoding="utf-8",
            ) as f:
                while True:
                    block = f.read(1_000_000)
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
