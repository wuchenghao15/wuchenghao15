"""
Text chunker with overlap support.

Splits text into chunks with configurable overlap for context continuity.
"""

from __future__ import annotations

from uuid import NAMESPACE_OID, uuid5

from m_flow.ingestion.chunks import split_paragraphs
from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.shared.logging_utils import get_logger

from .models.ContentFragment import ContentFragment

logger = get_logger()


class TextChunkerWithOverlap(Chunker):
    """Chunker that maintains overlap between consecutive chunks."""

    def __init__(
        self,
        document,
        get_text: callable,
        max_chunk_size: int,
        chunk_overlap_ratio: float = 0.0,
        get_chunk_data: callable = None,
    ):
        """
        Initialize overlapping chunker.

        Args:
            document: Source document.
            get_text: Async generator for text content.
            max_chunk_size: Maximum tokens per chunk.
            chunk_overlap_ratio: Fraction of chunk to overlap (0-1).
            get_chunk_data: Custom paragraph splitter.
        """
        super().__init__(document, get_text, max_chunk_size)

        self._buffer = []
        self._buffer_size = 0
        self.overlap_ratio = chunk_overlap_ratio
        self.overlap_size = int(max_chunk_size * chunk_overlap_ratio)

        # Configure paragraph splitter
        if get_chunk_data is not None:
            self.split_paragraphs = get_chunk_data
        elif chunk_overlap_ratio > 0:
            para_size = int(0.5 * chunk_overlap_ratio * max_chunk_size)
            self.split_paragraphs = lambda txt: split_paragraphs(txt, para_size, batch_paragraphs=True)
        else:
            self.split_paragraphs = lambda txt: split_paragraphs(txt, self.max_chunk_size, batch_paragraphs=True)

    def _would_overflow(self, para: dict) -> bool:
        """Check if adding paragraph exceeds limit."""
        return self._buffer_size + para["chunk_size"] > self.max_chunk_size

    def _add_to_buffer(self, para: dict):
        """Append paragraph to buffer."""
        self._buffer.append(para)
        self._buffer_size += para["chunk_size"]

    def _reset_buffer(self):
        """Clear buffer, preserving overlap portion."""
        if self.overlap_size == 0:
            self._buffer = []
            self._buffer_size = 0
            return

        # Keep trailing paragraphs within overlap
        kept = []
        kept_size = 0

        for para in reversed(self._buffer):
            if kept_size + para["chunk_size"] <= self.overlap_size:
                kept.insert(0, para)
                kept_size += para["chunk_size"]
            else:
                break

        self._buffer = kept
        self._buffer_size = kept_size

    def _build_fragment(self, text: str, size: int, cut_type: str, frag_id=None):
        """Construct ContentFragment."""
        try:
            return ContentFragment(
                id=frag_id or uuid5(NAMESPACE_OID, f"{self.document.id}-{self.chunk_index}"),
                text=text,
                chunk_size=size,
                is_part_of=self.document,
                chunk_index=self.chunk_index,
                cut_type=cut_type,
                contains=[],
                metadata={"index_fields": ["text"]},
            )
        except Exception as e:
            logger.error("Fragment creation failed: %s", e)
            raise

    def _emit_from_buffer(self):
        """Create fragment from buffer contents."""
        combined = " ".join(p["text"] for p in self._buffer)
        return self._build_fragment(
            text=combined,
            size=self._buffer_size,
            cut_type=self._buffer[-1]["cut_type"],
        )

    def _flush_and_emit(self, para: dict):
        """Emit current buffer and start new chunk."""
        if self._buffer:
            fragment = self._emit_from_buffer()
            self._reset_buffer()
            self._add_to_buffer(para)
        else:
            # Single oversized paragraph
            fragment = self._build_fragment(
                text=para["text"],
                size=para["chunk_size"],
                cut_type=para["cut_type"],
                frag_id=para.get("chunk_id"),
            )

        self.chunk_index += 1
        return fragment

    async def read(self):
        """Generate content fragments from document."""
        async for text_block in self.get_text():
            for para in self.split_paragraphs(text_block):
                if not self._would_overflow(para):
                    self._add_to_buffer(para)
                    continue

                yield self._flush_and_emit(para)

        # Emit remaining buffer
        if self._buffer:
            yield self._emit_from_buffer()
