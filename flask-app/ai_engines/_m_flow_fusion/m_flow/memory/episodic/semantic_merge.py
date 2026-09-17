# m_flow/memory/episodic/semantic_merge.py
"""
Stage 5.11.2: Semantic synonym merging

Core functions:
- Within episode, within same facet_type, conservative threshold (0.90 starting)
- Only use existing facet's search_text for vector matching (most stable)
- Aliases don't participate in vector matching (reduces false merge risk)

Note:
- Semantic merging is optional, controlled by environment variable
- Default disabled, needs explicit enabling
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from m_flow.shared.logging_utils import get_logger
from m_flow.adapters.vector import get_vector_provider

logger = get_logger("episodic.semantic_merge")


def _cosine(u: List[float], v: List[float]) -> float:
    """Calculate cosine similarity of two vectors"""
    dot = 0.0
    nu = 0.0
    nv = 0.0
    n = min(len(u), len(v))
    for i in range(n):
        dot += u[i] * v[i]
        nu += u[i] * u[i]
        nv += v[i] * v[i]
    if nu == 0.0 or nv == 0.0:
        return 0.0
    return dot / (math.sqrt(nu) * math.sqrt(nv))


@dataclass
class ExistingFacetInfo:
    """Existing Facet information (for semantic matching)"""

    id: str
    facet_type: str
    search_text: str
    aliases: List[str]


class SemanticFacetMatcher:
    """
    Semantic synonym matcher within episode.

    Features:
    - Only cache embedding for existing facets (same facet_type)
    - When candidate doesn't match string, try semantic matching
    - Conservative threshold (default 0.90), ensuring "no false merge" prioritized over "full merge"

    Usage:
    1. Call prepare() to precompute existing facets' embeddings
    2. Call match() for each candidate to try matching
    """

    def __init__(self, enabled: bool, threshold: float = 0.90):
        """
        Initialize matcher.

        Args:
            enabled: Whether to enable semantic matching
            threshold: Cosine similarity threshold (default 0.90, very conservative)
        """
        self.enabled = enabled
        self.threshold = threshold
        # facet_type -> (ids, search_texts, embeddings)
        self._cache: Dict[str, Tuple[List[str], List[str], List[List[float]]]] = {}

    async def _embed(self, texts: List[str]) -> List[List[float]]:
        """Call vector engine to generate embedding"""
        ve = get_vector_provider()
        return await ve.embedding_engine.embed_text(texts)

    async def prepare(self, existing_facets: List[ExistingFacetInfo]) -> None:
        """
        Precompute existing facets' embeddings (grouped by facet_type).

        Args:
            existing_facets: List of existing facets
        """
        if not self.enabled:
            return

        # Group by facet_type
        by_type: Dict[str, List[ExistingFacetInfo]] = {}
        for f in existing_facets:
            by_type.setdefault(f.facet_type, []).append(f)

        for facet_type, facets in by_type.items():
            # Only use search_text for vector (most stable), aliases don't participate in vector matching
            valid_facets = [f for f in facets if (f.search_text or "").strip()]
            if not valid_facets:
                continue

            ids = [f.id for f in valid_facets]
            texts = [f.search_text for f in valid_facets]

            try:
                vecs = await self._embed(texts)
                self._cache[facet_type] = (ids, texts, vecs)
            except Exception as e:
                logger.warning(f"Failed to embed existing facets for type {facet_type}: {e}")

    async def match(self, candidate_text: str, candidate_type: str) -> Optional[str]:
        """
        Try to semantically match candidate with existing facet.

        Args:
            candidate_text: Candidate facet's search_text
            candidate_type: Candidate facet's facet_type

        Returns:
            Matched existing facet id, or None (not matched)
        """
        if not self.enabled:
            return None

        if candidate_type not in self._cache:
            return None

        ids, texts, vecs = self._cache[candidate_type]
        if not ids or not vecs:
            return None

        try:
            cand_vec = (await self._embed([candidate_text]))[0]
        except Exception as e:
            logger.warning(f"Failed to embed candidate text: {e}")
            return None

        best_id = None
        best_sim = -1.0
        for fid, vec in zip(ids, vecs, strict=True):
            sim = _cosine(cand_vec, vec)
            if sim > best_sim:
                best_sim = sim
                best_id = fid

        if best_id and best_sim >= self.threshold:
            logger.debug(f"Semantic match: '{candidate_text}' -> existing facet {best_id} (sim={best_sim:.3f})")
            return str(best_id)

        return None
