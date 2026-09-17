"""Built-in text segmentation engine with paragraph, sentence, and fixed-window modes."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from m_flow.shared.data_models import ChunkMode

# Pre-compiled pattern for sentence boundary detection.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?…])\s+")


def _regex_split(text: str, pattern: str, *, retain: bool = False) -> List[str]:
    """Tokenise *text* with a regex, optionally keeping delimiters attached."""
    if not pattern:
        return list(text)

    if retain:
        raw = re.split(f"({pattern})", text)
        # Glue every delimiter back onto the preceding token.
        merged: list[str] = [raw[0]] if raw else []
        idx = 1
        while idx + 1 < len(raw):
            merged.append(raw[idx] + raw[idx + 1])
            idx += 2
        if idx < len(raw):
            merged.append(raw[idx])
        return [t for t in merged if t]

    return [t for t in re.split(pattern, text) if t]


def _number_items(items: list[str]) -> List[List]:
    """Attach 1-based ordinals to a list of strings."""
    return [[pos, item] for pos, item in enumerate(items, start=1)]


class DefaultChunkEngine:
    """Segment text with paragraph / sentence / exact-window strategies.

    The engine is **stateless** with respect to the text being processed:
    all configuration is captured in the constructor, and ``chunk_data``
    is a pure function of its ``source_data`` argument.
    """

    def __init__(
        self,
        chunk_strategy: Optional[ChunkMode] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        self._mode = chunk_strategy
        self._window = chunk_size
        self._overlap = chunk_overlap or 0

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def chunk_data(
        self,
        chunk_strategy=None,
        source_data=None,
        chunk_size=None,
        chunk_overlap=None,
    ) -> Tuple[list, list]:
        """Route to the appropriate segmentation back-end."""
        dispatch = {
            ChunkMode.PARAGRAPH: self._paragraphs,
            ChunkMode.SENTENCE: self._sentences,
            ChunkMode.EXACT: self._fixed_window,
        }
        handler = dispatch.get(self._mode)
        if handler is None:
            err = "Invalid chunk strategy."
            return err, [[0, err]]
        return handler(source_data, self._window, self._overlap)

    # ------------------------------------------------------------------
    # Fixed-width window
    # ------------------------------------------------------------------

    def _fixed_window(self, fragments: list, win: int, lap: int) -> Tuple[List[str], List[List]]:
        """Cut the concatenated text into overlapping fixed-size windows."""
        blob = "".join(fragments)
        step = max(win - lap, 1)
        pieces = [blob[offset : offset + win] for offset in range(0, len(blob), step)]
        return pieces, _number_items(pieces)

    # ------------------------------------------------------------------
    # Sentence-level splitting
    # ------------------------------------------------------------------

    def _sentences(self, fragments: list, win: int, lap: int) -> Tuple[List[str], List[List]]:
        """Split on sentence boundaries; oversized sentences fall back to fixed window."""
        blob = "".join(fragments)
        raw_sentences = _SENTENCE_BREAK.split(blob)

        output: list[str] = []
        for sent in raw_sentences:
            if len(sent) <= win:
                output.append(sent)
            else:
                sub, _ = self._fixed_window([sent], win, lap)
                output.extend(sub)

        return output, _number_items(output)

    # ------------------------------------------------------------------
    # Paragraph-level splitting
    # ------------------------------------------------------------------

    def _paragraphs(
        self,
        fragments: list,
        win: int,
        lap: int,
        threshold: float = 0.75,
    ) -> Tuple[List[str], List[List]]:
        """Split on paragraph boundaries, extending to the next full stop."""
        blob = "".join(fragments)
        length = len(blob)
        sep = "\n\n" if "\n\n" in blob else "\n"
        min_scan = int(threshold * win)
        cursor = 0
        pieces: list[str] = []

        while cursor < length:
            limit = min(cursor + win, length)

            # Try to snap to a paragraph boundary.
            brk = blob.find(sep, cursor + min_scan, limit)
            if brk >= 0:
                limit = brk + len(sep)

            tail = limit + lap

            segment = blob[cursor:tail]

            # Extend until a period or end-of-text.
            while segment and segment[-1] != "." and tail < length:
                segment += blob[tail]
                tail += 1

            pieces.append(segment.replace("\n", "").strip())
            cursor = tail - lap

        return pieces, _number_items(pieces)
