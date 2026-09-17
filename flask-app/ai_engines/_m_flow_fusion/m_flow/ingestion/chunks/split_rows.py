"""
Row-based text chunking for M-flow ingestion.

Splits text into chunks by rows (double newline separated) while
respecting token size limits and enabling exact reconstruction.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator
from uuid import NAMESPACE_OID, uuid5

from m_flow.adapters.vector.embeddings import get_embedding_engine


def _token_count(text: str) -> int:
    """
    Count tokens in a text fragment.

    Uses the embedding engine tokenizer if available, otherwise
    estimates 3 tokens per key-value pair as a fallback.
    """
    engine = get_embedding_engine()
    if engine.tokenizer:
        return engine.tokenizer.count_tokens(text)
    return 3


def split_rows(
    data: str,
    max_chunk_size: int,
) -> Iterator[Dict[str, Any]]:
    """
    Split text into chunks by rows with size constraints.

    Rows are separated by double newlines. Within each row,
    comma-separated fields are grouped until max_chunk_size
    is reached.

    Yields dictionaries with:
      - text: Chunk content
      - chunk_size: Token count
      - chunk_id: Deterministic UUID based on content
      - chunk_index: Sequential index
      - cut_type: "row_cut" for mid-row splits, "row_end" for row boundaries

    Args:
        data: Input text with double-newline separated rows.
        max_chunk_size: Maximum tokens per chunk.

    Yields:
        Chunk dictionaries.
    """
    buffer: list[str] = []
    buffer_tokens = 0
    idx = 0

    rows = data.split("\n\n")

    for row in rows:
        fields = row.split(", ")

        for field in fields:
            field_tokens = _token_count(field)

            # Flush buffer if adding this field would exceed limit
            if buffer_tokens > 0 and (buffer_tokens + field_tokens > max_chunk_size):
                chunk_text = ", ".join(buffer)
                yield {
                    "text": chunk_text,
                    "chunk_size": buffer_tokens,
                    "chunk_id": uuid5(NAMESPACE_OID, chunk_text),
                    "chunk_index": idx,
                    "cut_type": "row_cut",
                }
                buffer = []
                buffer_tokens = 0
                idx += 1

            buffer.append(field)
            buffer_tokens += field_tokens

        # Emit row-end chunk
        if buffer:
            chunk_text = ", ".join(buffer)
            yield {
                "text": chunk_text,
                "chunk_size": buffer_tokens,
                "chunk_id": uuid5(NAMESPACE_OID, chunk_text),
                "chunk_index": idx,
                "cut_type": "row_end",
            }
            buffer = []
            buffer_tokens = 0
            idx += 1
