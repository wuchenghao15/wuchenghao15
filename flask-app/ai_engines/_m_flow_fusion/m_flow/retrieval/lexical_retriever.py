"""
Lexical retrieval engine.

BM25-style retrieval using tokenizer and scorer functions.
"""

from __future__ import annotations

import asyncio
from heapq import nlargest
from typing import Any, Callable, Optional

from m_flow.adapters.graph import get_graph_provider
from m_flow.retrieval.base_retriever import BaseRetriever
from m_flow.retrieval.exceptions.exceptions import NoDataError
from m_flow.shared.logging_utils import get_logger

logger = get_logger("LexicalRetriever")


class LexicalRetriever(BaseRetriever):
    """
    Token-based retriever with pluggable scoring.

    Loads ContentFragments from graph and scores them
    against queries using provided tokenizer/scorer.
    """

    def __init__(
        self,
        tokenizer: Callable,
        scorer: Callable,
        top_k: int = 10,
        with_scores: bool = False,
    ):
        """
        Configure retriever.

        Args:
            tokenizer: Text -> token list function.
            scorer: (query_tokens, doc_tokens) -> score function.
            top_k: Number of results to return.
            with_scores: Include scores in output.
        """
        if not callable(tokenizer) or not callable(scorer):
            raise TypeError("tokenizer and scorer must be callable")
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be positive integer")

        self.tokenize = tokenizer
        self.score_fn = scorer
        self.top_k = top_k
        self.include_scores = bool(with_scores)

        self._doc_tokens: dict[str, list] = {}
        self._doc_payloads: dict[str, dict] = {}
        self._ready = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Load ContentFragments from graph engine."""
        async with self._lock:
            if self._ready:
                return

            logger.info("Loading ContentFragments for lexical search")

            try:
                engine = await get_graph_provider()
                nodes, _ = await engine.query_by_attributes([{"type": ["ContentFragment"]}])
            except Exception as err:
                logger.error("Graph engine failed: %s", err)
                raise NoDataError("Cannot load graph") from err

            loaded = 0
            for node in nodes:
                try:
                    node_id, doc = node
                except (TypeError, ValueError):
                    logger.warning("Invalid node structure: %r", node)
                    continue

                if doc.get("type") != "ContentFragment":
                    continue

                text = doc.get("text", "")
                if not text:
                    continue

                try:
                    tokens = self.tokenize(text)
                    if not tokens:
                        continue

                    doc_id = str(doc.get("id", node_id))
                    self._doc_tokens[doc_id] = tokens
                    self._doc_payloads[doc_id] = doc
                    loaded += 1
                except Exception as err:
                    logger.error("Tokenization failed: %s", err)

            if loaded == 0:
                raise NoDataError("No chunks loaded")

            self._ready = True
            logger.info("Loaded %d chunks", loaded)

    async def get_context(self, query: str) -> Any:
        """
        Retrieve relevant chunks for query.

        Args:
            query: Search query.

        Returns:
            Top-k matching documents.
        """
        if not self._ready:
            await self.initialize()

        if not self._doc_tokens:
            logger.warning("No documents indexed")
            return []

        try:
            q_tokens = self.tokenize(query)
        except Exception as err:
            logger.error("Query tokenization failed: %s", err)
            return []

        if not q_tokens:
            logger.warning("Empty query tokens")
            return []

        # Score all documents
        scores = []
        for doc_id, doc_tokens in self._doc_tokens.items():
            try:
                s = self.score_fn(q_tokens, doc_tokens)
                s = float(s) if isinstance(s, (int, float)) else 0.0
            except Exception as err:
                logger.error("Scoring error for %s: %s", doc_id, err)
                s = 0.0
            scores.append((doc_id, s))

        # Return top results
        top = nlargest(self.top_k, scores, key=lambda x: x[1])

        logger.info("Found %d results (top_k=%d)", len(top), self.top_k)

        if self.include_scores:
            return [(self._doc_payloads[did], sc) for did, sc in top]
        return [self._doc_payloads[did] for did, _ in top]

    async def get_completion(
        self,
        query: str,
        context: Optional[Any] = None,
        session_id: Optional[str] = None,
    ) -> Any:
        """
        Return context for query.

        Args:
            query: Search query.
            context: Pre-fetched context (optional).
            session_id: Session identifier (unused).

        Returns:
            Retrieved or provided context.
        """
        if context is None:
            context = await self.get_context(query)
        return context
