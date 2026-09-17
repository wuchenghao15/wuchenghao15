"""Text segmentation back-end powered by Langchain's recursive splitters.

This module provides the ``LangchainChunkEngine`` class, which delegates
to :class:`langchain_text_splitters.RecursiveCharacterTextSplitter` for
both source-code and natural-language chunking.  The heavy Langchain
dependency is imported **lazily** inside each method so that users who
never select this back-end pay no import cost.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from m_flow.shared.data_models import ChunkMode


def _extract_pages(documents) -> Tuple[List[str], List[list]]:
    """Pull ``.page_content`` from Langchain ``Document`` objects and number them."""
    contents = [doc.page_content for doc in documents]
    indexed = [[seq, doc] for seq, doc in enumerate(documents, start=1)]
    return contents, indexed


class LangchainChunkEngine:
    """Segment text via Langchain's ``RecursiveCharacterTextSplitter``.

    Two strategies are currently supported:

    * **CODE** — language-aware splitting (defaults to Python).
    * **LANGCHAIN_CHARACTER** — generic character-count splitting.
    """

    def __init__(
        self,
        chunk_strategy: Optional[ChunkMode] = None,
        source_data=None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        self._strategy = chunk_strategy
        self._data = source_data
        self._max_chars = chunk_size
        self._overlap_chars = chunk_overlap

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def chunk_data(
        self,
        chunk_strategy=None,
        source_data=None,
        chunk_size=None,
        chunk_overlap=None,
    ) -> Tuple[list, list]:
        """Select and run the appropriate Langchain splitter."""
        _HANDLERS = {
            ChunkMode.CODE: self._split_code,
            ChunkMode.LANGCHAIN_CHARACTER: self._split_characters,
        }
        handler = _HANDLERS.get(chunk_strategy)
        if handler is None:
            fallback = "Invalid chunk strategy."
            return fallback, [0, fallback]
        return handler(source_data, self._max_chars, self._overlap_chars)

    # ------------------------------------------------------------------
    # Code-aware splitting
    # ------------------------------------------------------------------

    def _split_code(
        self,
        raw_text,
        max_chars: int,
        overlap: int = 10,
        lang=None,
    ) -> Tuple[List[str], List[list]]:
        """Chunk source code using Langchain's language-aware splitter."""
        from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

        target_lang = lang if lang is not None else Language.PYTHON
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=target_lang,
            chunk_size=max_chars,
            chunk_overlap=overlap,
        )
        docs = splitter.create_documents([raw_text])
        return _extract_pages(docs)

    # ------------------------------------------------------------------
    # Character-count splitting
    # ------------------------------------------------------------------

    def _split_characters(
        self,
        raw_text,
        max_chars: int = 1500,
        overlap: int = 10,
    ) -> Tuple[List[str], List[list]]:
        """Chunk text by character count with recursive separator fallback."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chars,
            chunk_overlap=overlap,
        )
        docs = splitter.create_documents([raw_text])
        return _extract_pages(docs)
