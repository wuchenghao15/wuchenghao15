# m_flow/memory/procedural/procedure_builder/recall.py
"""
Recall: Find similar existing Procedures via vector search.

Mirrors episodic/episode_builder/phase0a.py pattern.
Uses procedural_bundle_search for recall, then extracts structured info from edges.
"""

from __future__ import annotations

import json
from typing import Dict, List

from m_flow.core import Edge
from m_flow.shared.logging_utils import get_logger
from m_flow.retrieval.utils.procedural_bundle_search import procedural_bundle_search

from .pipeline_contexts import ExistingProcedureInfo

logger = get_logger("procedural.incremental.recall")

# Recall similarity threshold (lower score = more similar, keep score < threshold)
RECALL_SIMILARITY_THRESHOLD = 0.4


async def recall_similar_procedures(
    search_text: str,
    top_k: int = 3,
    score_threshold: float = RECALL_SIMILARITY_THRESHOLD,
) -> List[ExistingProcedureInfo]:
    """
    Recall similar existing procedures using procedural_bundle_search.

    Args:
        search_text: Query text for searching
        top_k: Max number of results
        score_threshold: Filter out results with score >= threshold (lower is better)

    Returns:
        List of ExistingProcedureInfo sorted by relevance
    """
    if not search_text or not search_text.strip():
        return []

    try:
        result = await procedural_bundle_search(
            query=search_text,
            top_k=top_k,
            return_bundles=True,
        )

        # Handle both tuple (edges, bundles) and list return types
        if isinstance(result, tuple):
            edges, bundles = result
        else:
            # Old API returns just edges
            return []

        if not bundles:
            return []

        # Filter by threshold
        relevant_bundles = [b for b in bundles if b.get("score", 1.0) < score_threshold]

        if not relevant_bundles:
            logger.debug(
                f"[procedural.incremental.recall] All recalled bundles filtered out by threshold ({score_threshold})"
            )
            return []

        # Extract procedure info from edges
        infos = _extract_procedure_info_from_edges(edges, relevant_bundles)
        if infos:
            logger.info(
                f"[procedural.incremental.recall] Found {len(infos)} similar procedures: "
                + ", ".join(f"'{p.title[:30]}' (score={p.relevance_score:.3f})" for p in infos[:3])
            )
        return infos

    except Exception as e:
        logger.warning(f"[procedural.incremental.recall] Recall failed: {e}")
        return []


def _extract_procedure_info_from_edges(
    edges: List[Edge],
    bundles: List[dict],
) -> List[ExistingProcedureInfo]:
    """
    Extract Procedure information from recalled edges.
    Adapts to 2-layer structure (Procedure → Point, no Pack).
    """
    bundle_proc_ids = {b["procedure_id"] for b in bundles}
    procs: Dict[str, ExistingProcedureInfo] = {}

    for e in edges:
        for n in [e.node1, e.node2]:
            ntype = n.attributes.get("type", "")
            pid = str(n.id)

            if ntype == "Procedure" and pid in bundle_proc_ids and pid not in procs:
                # Parse properties (may be JSON string)
                props = n.attributes.get("properties") or {}
                if isinstance(props, str):
                    try:
                        props = json.loads(props)
                    except (json.JSONDecodeError, TypeError):
                        props = {}

                # Find bundle info for this procedure
                bundle_info = next((b for b in bundles if b["procedure_id"] == pid), {})

                procs[pid] = ExistingProcedureInfo(
                    procedure_id=pid,
                    title=n.attributes.get("name", ""),
                    signature=props.get("signature") or n.attributes.get("signature", ""),
                    search_text=props.get("search_text") or n.attributes.get("search_text", ""),
                    version=props.get("version", 1) or n.attributes.get("version", 1),
                    points_text=props.get("points_text") or n.attributes.get("points_text", ""),
                    context_text=props.get("context_text") or n.attributes.get("context_text", ""),
                    summary=props.get("summary") or n.attributes.get("summary", ""),
                    relevance_score=bundle_info.get("score", 1.0),
                )

    # Sort by relevance (lower score = more relevant)
    return sorted(procs.values(), key=lambda p: p.relevance_score)
