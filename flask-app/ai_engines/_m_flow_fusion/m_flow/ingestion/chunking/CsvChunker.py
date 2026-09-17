"""
CSV Document Chunker
====================

Splits CSV content into row-based chunks for processing.
Each row (or group of rows) becomes a separate ContentFragment.
"""

from __future__ import annotations

from m_flow.shared.logging_utils import get_logger
from m_flow.ingestion.chunks import split_rows
from m_flow.ingestion.chunking.Chunker import Chunker

from .models.ContentFragment import ContentFragment

_logger = get_logger()


class CsvChunker(Chunker):
    """
    Chunker specialized for CSV/tabular data.

    Splits CSV content by rows while respecting the maximum chunk size
    constraint. Each chunk preserves row boundaries to maintain data
    integrity.
    """

    async def read(self):
        """
        Yield ContentFragment instances for each chunk of CSV data.

        Iterates through the document's text content and splits it
        into row-based chunks. Validates that each chunk respects
        the maximum size constraint.

        Yields
        ------
        ContentFragment
            A fragment representing one or more CSV rows.

        Raises
        ------
        ValueError
            If a single row exceeds the maximum chunk size.
        """
        async for raw_text in self.get_text():
            # Skip empty content
            if raw_text is None:
                continue

            # Process each row-based chunk
            for row_chunk in split_rows(raw_text, self.max_chunk_size):
                chunk_size = row_chunk["chunk_size"]

                # Validate size constraint
                if chunk_size > self.max_chunk_size:
                    raise ValueError(
                        f"Row data ({chunk_size} chars) exceeds maximum chunk size ({self.max_chunk_size})"
                    )

                # Build content fragment
                fragment = ContentFragment(
                    id=row_chunk["chunk_id"],
                    text=row_chunk["text"],
                    chunk_size=chunk_size,
                    is_part_of=self.document,
                    chunk_index=self.chunk_index,
                    cut_type=row_chunk["cut_type"],
                    contains=[],
                    metadata={"index_fields": ["text"]},
                )

                self.chunk_index += 1
                yield fragment
