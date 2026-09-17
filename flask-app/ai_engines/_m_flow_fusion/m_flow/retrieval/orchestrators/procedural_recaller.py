"""
Procedural Recaller

Multi-query recall + deduplication + active preference.

Strategy:
1. Call procedural_bundle_search(return_bundles=True) for each query
2. Union merge, deduplicate by procedure_id
3. Score merge: final_score = min(score_q)
4. Active preference: inactive already has penalty applied internally

Output:
- List of ProcedureHit, containing procedure_id, score, edges, from_query_kinds
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge
from m_flow.retrieval.querying.procedural_query_builder import QuerySpec
from m_flow.retrieval.utils.procedural_bundle_search import procedural_bundle_search
from m_flow.shared.logging_utils import get_logger

logger = get_logger("ProceduralRecaller")


@dataclass
class ProcedureHit:
    """
    Procedure recall result.

    Attributes:
        procedure_id: Procedure node ID
        score: Final score (lower is better)
        edges: Related edge list
        from_query_kinds: List of query types that matched
        bundle_metadata: Original bundle metadata
    """

    procedure_id: str
    score: float
    edges: List[Edge] = field(default_factory=list)
    from_query_kinds: List[str] = field(default_factory=list)
    bundle_metadata: Optional[Dict] = None


class ProceduralRecaller:
    """
    Procedural Recaller

    Multi-query recall + merge + deduplication.

    Supports:
    - Deduplication by procedure_id
    - Optional aggregation by procedure_key (merge multiple versions with same key)
    - Weight adjustment for scores
    """

    def __init__(
        self,
        top_k_per_query: int = 3,
        max_total_procedures: int = 5,
        procedural_nodeset_name: str = "Procedural",
        wide_search_top_k: int = 50,
        aggregate_by_key: bool = False,  # Optional: aggregate by procedure_key
    ):
        """
        Initialize Recaller.

        Args:
            top_k_per_query: Top_k for each query
            max_total_procedures: Maximum number of procedures to return
            procedural_nodeset_name: Procedural MemorySpace name
            wide_search_top_k: Initial recall count per collection
        """
        self.top_k_per_query = top_k_per_query
        self.max_total_procedures = max_total_procedures
        self.procedural_nodeset_name = procedural_nodeset_name
        self.wide_search_top_k = wide_search_top_k
        self.aggregate_by_key = aggregate_by_key

    async def recall(
        self,
        queries: List[QuerySpec],
    ) -> List[ProcedureHit]:
        """
        Execute multi-query recall.

        Args:
            queries: List of QuerySpec

        Returns:
            List of ProcedureHit, sorted by score
        """
        if not queries:
            return []

        # 1. Execute all queries in parallel
        tasks = []
        for q in queries:
            tasks.append(self._search_single_query(q))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 2. Merge results
        # procedure_id -> ProcedureHit
        merged: Dict[str, ProcedureHit] = {}

        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.warning(f"[recaller] Query failed: {queries[i].q[:30]}... error={res}")
                continue

            edges, bundles_meta = res
            query_kind = queries[i].kind

            # Extract procedure_id from edges
            proc_edges: Dict[str, List[Edge]] = {}
            for edge in edges:
                for node in (edge.node1, edge.node2):
                    if node.attributes.get("type") == "Procedure":
                        pid = str(node.id)
                        if pid not in proc_edges:
                            proc_edges[pid] = []
                        proc_edges[pid].append(edge)
                        break

            # Get scores from bundles_meta
            score_by_id: Dict[str, float] = {}
            meta_by_id: Dict[str, Dict] = {}
            for bm in bundles_meta:
                pid = bm.get("procedure_id")
                if pid:
                    score_by_id[pid] = bm.get("score", 999.0)
                    meta_by_id[pid] = bm

            # Merge into merged
            for pid, pedges in proc_edges.items():
                raw_score = score_by_id.get(pid, 999.0)
                # final_score = min_over_queries(score_q / weight_q_adjust)
                # weight > 1 means more important, should reduce score (better)
                weight = queries[i].weight if queries[i].weight > 0 else 1.0
                adjusted_score = raw_score / weight

                if pid in merged:
                    # Update score: take minimum (after weight adjustment)
                    if adjusted_score < merged[pid].score:
                        merged[pid].score = adjusted_score
                        merged[pid].bundle_metadata = meta_by_id.get(pid)

                    # Merge edges (deduplicate)
                    existing_keys: Set[str] = {self._edge_key(e) for e in merged[pid].edges}
                    for e in pedges:
                        ek = self._edge_key(e)
                        if ek not in existing_keys:
                            merged[pid].edges.append(e)
                            existing_keys.add(ek)

                    # Merge query_kinds
                    if query_kind not in merged[pid].from_query_kinds:
                        merged[pid].from_query_kinds.append(query_kind)
                else:
                    merged[pid] = ProcedureHit(
                        procedure_id=pid,
                        score=adjusted_score,
                        edges=pedges,
                        from_query_kinds=[query_kind],
                        bundle_metadata=meta_by_id.get(pid),
                    )

        # 3. Optional: aggregate by procedure_key (keep only best for multiple versions with same key)
        if self.aggregate_by_key:
            merged = self._aggregate_by_procedure_key(merged)

        # 4. Sort by score
        hits = list(merged.values())
        hits.sort(key=lambda h: h.score)

        # 5. Limit count
        hits = hits[: self.max_total_procedures]

        logger.info(f"[recaller] Recalled {len(hits)} procedures from {len(queries)} queries")

        return hits

    def _aggregate_by_procedure_key(
        self,
        merged: Dict[str, ProcedureHit],
    ) -> Dict[str, ProcedureHit]:
        """
        Aggregate by procedure_key, keep only best score for multiple versions with same key.
        """
        key_to_best: Dict[str, ProcedureHit] = {}

        for pid, hit in merged.items():
            # Try to get procedure_key from bundle_metadata
            pkey = None
            if hit.bundle_metadata:
                pkey = hit.bundle_metadata.get("procedure_key")

            # If no key, use procedure_id
            if not pkey:
                pkey = pid

            if pkey in key_to_best:
                # Keep the one with better score
                if hit.score < key_to_best[pkey].score:
                    # Merge edges and query_kinds
                    old_hit = key_to_best[pkey]
                    hit.edges = hit.edges + [
                        e for e in old_hit.edges if self._edge_key(e) not in {self._edge_key(x) for x in hit.edges}
                    ]
                    hit.from_query_kinds = list(set(hit.from_query_kinds + old_hit.from_query_kinds))
                    key_to_best[pkey] = hit
                else:
                    # Merge edges and query_kinds into existing
                    existing = key_to_best[pkey]
                    existing.edges = existing.edges + [
                        e for e in hit.edges if self._edge_key(e) not in {self._edge_key(x) for x in existing.edges}
                    ]
                    existing.from_query_kinds = list(set(existing.from_query_kinds + hit.from_query_kinds))
            else:
                key_to_best[pkey] = hit

        return key_to_best

    async def _search_single_query(self, query: QuerySpec):
        """Execute search for a single query."""
        return await procedural_bundle_search(
            query=query.q,
            top_k=self.top_k_per_query,
            procedural_nodeset_name=self.procedural_nodeset_name,
            wide_search_top_k=self.wide_search_top_k,
            return_bundles=True,
        )

    def _edge_key(self, edge: Edge) -> str:
        """Generate unique key for edge."""
        n1 = str(edge.node1.id) if edge.node1 else ""
        n2 = str(edge.node2.id) if edge.node2 else ""
        rel = edge.attributes.get("relationship_name", "")
        return f"{n1}_{n2}_{rel}"


async def recall_procedures(
    queries: List[QuerySpec],
    top_k_per_query: int = 3,
    max_total: int = 5,
) -> List[ProcedureHit]:
    """
    Convenience function: execute procedural multi-query recall.

    Args:
        queries: List of QuerySpec
        top_k_per_query: Top_k for each query
        max_total: Maximum number of procedures to return

    Returns:
        List of ProcedureHit
    """
    recaller = ProceduralRecaller(
        top_k_per_query=top_k_per_query,
        max_total_procedures=max_total,
    )
    return await recaller.recall(queries)
