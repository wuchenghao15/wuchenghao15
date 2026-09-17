"""
Sentence-level text segmentation for M-flow ingestion.

Splits text into sentences respecting word and paragraph boundaries,
with optional token-based size limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional, Tuple
from uuid import UUID, uuid4

from m_flow.adapters.vector.embeddings import get_embedding_engine
from m_flow.ingestion.chunks.split_words import split_words


def _measure(text: str) -> int:
    """Token count via the embedding engine's tokenizer (fallback: 1)."""
    engine = get_embedding_engine()
    return engine.tokenizer.count_tokens(text) if engine.tokenizer else 1


@dataclass
class _SentenceAccumulator:
    """Builds up a sentence from word-level tokens."""

    text: str = ""
    tokens: int = 0
    para_id: UUID = field(default_factory=uuid4)
    marker: Optional[str] = None

    def add(self, word: str, word_tokens: int) -> None:
        self.text += word
        self.tokens += word_tokens

    def set_marker(self, boundary: str | None) -> None:
        if boundary in ("paragraph_end", "sentence_end"):
            self.marker = boundary
        elif any(c.isalpha() for c in (boundary or "")):
            self.marker = boundary

    def emit(self) -> Tuple[UUID, str, int, Optional[str]]:
        result = (self.para_id, self.text, self.tokens, self.marker)
        self.text = ""
        self.tokens = 0
        return result

    def new_paragraph(self) -> None:
        self.para_id = uuid4()


def split_sentences(
    text: str,
    max_tokens: Optional[int] = None,
) -> Iterator[Tuple[UUID, str, int, Optional[str]]]:
    """
    Segment text into sentence-sized pieces.

    Yields (paragraph_id, sentence_text, token_count, boundary_type).

    Boundary types:
      - "paragraph_end" / "sentence_end" / "sentence_cut" / "word"
    """
    acc = _SentenceAccumulator()

    for word, word_boundary in split_words(text):
        word_tokens = _measure(word)
        acc.set_marker(word_boundary)

        # Overflow → flush before appending
        if max_tokens and acc.tokens + word_tokens > max_tokens:
            yield acc.emit()
            acc.add(word, word_tokens)
            continue

        # Sentence or paragraph boundary → append then flush
        if word_boundary in ("paragraph_end", "sentence_end"):
            acc.add(word, word_tokens)
            if word_boundary == "paragraph_end":
                acc.new_paragraph()
            yield acc.emit()
        else:
            acc.add(word, word_tokens)

    # Trailing content
    if acc.text:
        if max_tokens and acc.tokens > max_tokens:
            raise ValueError(f"Single word exceeds chunk size limit ({max_tokens} tokens)")
        if acc.marker == "word":
            acc.marker = "sentence_cut"
        yield acc.emit()
