"""
Paragraph-based text chunker.

Splits text by paragraphs while respecting size limits.
"""

from __future__ import annotations

from uuid import NAMESPACE_OID, uuid5

from m_flow.ingestion.chunks import split_paragraphs
from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.shared.logging_utils import get_logger

from .models.ContentFragment import ContentFragment

logger = get_logger()


class TextChunker(Chunker):
    """
    Paragraph-aware text chunker.

    Accumulates paragraphs up to size limit, then yields
    combined fragments.
    """

    async def read(self):
        """
        Generate content fragments from paragraphs.

        Yields:
            ContentFragment for each chunk.
        """
        buffer = []
        buffer_size = 0

        async for text_block in self.get_text():
            paragraphs = split_paragraphs(
                text_block,
                self.max_chunk_size,
                batch_paragraphs=True,
            )

            for para in paragraphs:
                para_size = para["chunk_size"]

                # Check if adding paragraph exceeds limit
                if buffer_size + para_size <= self.max_chunk_size:
                    buffer.append(para)
                    buffer_size += para_size
                else:
                    # Emit current buffer or single oversized paragraph
                    if buffer:
                        yield self._create_from_buffer(buffer, buffer_size)
                        buffer = [para]
                        buffer_size = para_size
                    else:
                        # Single paragraph exceeds limit
                        yield self._create_single(para)

                    self.chunk_index += 1

        # Emit remaining buffer
        if buffer:
            yield self._create_from_buffer(buffer, buffer_size)

    def _create_from_buffer(self, buffer: list, size: int) -> ContentFragment:
        """Create fragment from accumulated paragraphs."""
        text = " ".join(p["text"] for p in buffer)
        cut_type = buffer[-1]["cut_type"]

        try:
            return ContentFragment(
                id=uuid5(NAMESPACE_OID, f"{self.document.id}-{self.chunk_index}"),
                text=text,
                chunk_size=size,
                is_part_of=self.document,
                chunk_index=self.chunk_index,
                cut_type=cut_type,
                contains=[],
                metadata={"index_fields": ["text"]},
            )
        except Exception as err:
            logger.error("Fragment creation failed: %s", err)
            raise

    def _create_single(self, para: dict) -> ContentFragment:
        """Create fragment from single paragraph."""
        return ContentFragment(
            id=para["chunk_id"],
            text=para["text"],
            chunk_size=para["chunk_size"],
            is_part_of=self.document,
            chunk_index=self.chunk_index,
            cut_type=para["cut_type"],
            contains=[],
            metadata={"index_fields": ["text"]},
        )
