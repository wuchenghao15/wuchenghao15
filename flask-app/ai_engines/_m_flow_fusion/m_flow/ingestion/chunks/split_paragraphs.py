"""
Paragraph-aware chunking with deterministic IDs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List
from uuid import NAMESPACE_OID, uuid5

from .split_sentences import split_sentences


@dataclass
class _ChunkBuffer:
    """Accumulates sentences until a size threshold or boundary triggers a flush."""

    content: str = ""
    tokens: int = 0
    sources: List[str] = field(default_factory=list)
    position: int = 0
    boundary: str = "default"

    @property
    def has_content(self) -> bool:
        return self.tokens > 0

    def append(self, text: str, size: int, source_id: str) -> None:
        self.content += text
        self.tokens += size
        self.sources.append(source_id)

    def flush(self, reason: str | None = None) -> Dict[str, Any]:
        result = {
            "text": self.content,
            "chunk_size": self.tokens,
            "chunk_id": uuid5(NAMESPACE_OID, self.content),
            "paragraph_ids": list(self.sources),
            "chunk_index": self.position,
            "cut_type": reason or self.boundary,
        }
        self.position += 1
        self.content = ""
        self.tokens = 0
        self.sources.clear()
        return result

    def update_boundary(self, marker: str | None) -> None:
        self.boundary = marker or "default"


def split_paragraphs(
    data: str,
    max_chunk_size: int,
    batch_paragraphs: bool = True,
) -> Iterator[Dict[str, Any]]:
    """
    Split *data* into chunks bounded by *max_chunk_size* tokens.

    Each yielded dict contains:
    - ``text`` – chunk content
    - ``chunk_size`` – token count
    - ``chunk_id`` – deterministic UUID5
    - ``paragraph_ids`` – source paragraph references
    - ``chunk_index`` – ordinal position
    - ``cut_type`` – reason for boundary

    When *batch_paragraphs* is False, each paragraph is emitted separately.
    """
    buf = _ChunkBuffer()

    for para_id, sent, sent_size, end_type in split_sentences(data, max_tokens=max_chunk_size):
        if buf.has_content and buf.tokens + sent_size > max_chunk_size:
            yield buf.flush()

        buf.append(sent, sent_size, para_id)

        if not batch_paragraphs and end_type in ("paragraph_end", "sentence_cut"):
            yield buf.flush(reason=end_type)

        buf.update_boundary(end_type)

    if buf.has_content:
        final = "sentence_cut" if buf.boundary == "word" else buf.boundary
        yield buf.flush(reason=final)
