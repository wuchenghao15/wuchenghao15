"""
Episodic Bundle Search - main process orchestration.

Responsibilities:
- Coordinate modules to complete retrieval flow
- No specific business logic
- End-to-end logging
"""

import asyncio
import heapq
from typing import Dict, List, Optional

from m_flow.shared.logging_utils import get_logger, ERROR
from m_flow.shared.tracing import TraceManager
from m_flow.adapters.vector.exceptions import CollectionNotFoundError
from m_flow.adapters.vector import get_vector_provider
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge

from .config import EpisodicConfig, get_episodic_config
from .memory_fragment import get_episodic_memory_fragment, compute_best_node_distances
from .query_preprocessor import preprocess_query, PreprocessedQuery
from .exact_match_bonus import apply_exact_match_bonus, apply_keyword_match_bonus
from .bundle_scorer import (
    build_relationship_index,
    compute_episode_bundles,
    RelationshipIndex,
)
from .output_assembler import assemble_output_edges
from .retrieval_logger import RetrievalLogger
from .adaptive_scoring import (
    compute_collection_stats,
    compute_adaptive_context,
    AdaptiveScoringContext,
)

logger = get_logger(level=ERROR)


async def episodic_bundle_search(
    query: str,
    top_k: Optional[int] = None,
    config: Optional[EpisodicConfig] = None,
    # The following parameters override config
    episodic_nodeset_name: Optional[str] = None,
    wide_search_top_k: Optional[int] = None,
    triplet_distance_penalty: Optional[float] = None,
    strict_nodeset_filtering: Optional[bool] = None,
    max_relevant_ids: Optional[int] = None,
    edge_miss_cost: Optional[float] = None,
    hop_cost: Optional[float] = None,
    max_facets_per_episode: Optional[int] = None,
    max_points_per_facet: Optional[int] = None,
    collections: Optional[List[str]] = None,
) -> List[Edge]:
    """
    Episodic Bundle Search - episodic memory retrieval based on path cost.

    Args:
        query: Query text
        top_k: Number of top-k to return
        config: Configuration object (optional)
        Other parameters: Individual parameters to override config

    Returns:
        List[Edge]: Sorted edge list
    """
    # Parameter validation
    if not query or not isinstance(query, str):
        raise ValueError("M-Flow search requires a non-blank query string.")

    # Load config and apply overrides
    cfg = config or get_episodic_config()
    cfg = _apply_overrides(
        cfg,
        top_k,
        episodic_nodeset_name,
        wide_search_top_k,
        triplet_distance_penalty,
        strict_nodeset_filtering,
        max_relevant_ids,
        edge_miss_cost,
        hop_cost,
        max_facets_per_episode,
        max_points_per_facet,
        collections,
    )

    if cfg.top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    # Initialize retrieval logger
    rlog = RetrievalLogger(query)

    TraceManager.event(
        "episodic.search.start",
        {
            "query": query[:100],
            "top_k": cfg.top_k,
        },
    )

    try:
        # Step 1: Query preprocessing (includes time parsing)
        preprocessed = preprocess_query(query, cfg)
        rlog.log_preprocess(
            original=query,
            vector_query=preprocessed.vector_query,
            use_hybrid=preprocessed.use_hybrid,
            hybrid_reason=preprocessed.hybrid_reason,
            keyword=preprocessed.keyword,
        )

        # Log time parsing results
        if preprocessed.has_time:
            rlog.log_time_parse(
                found=True,
                start_ms=preprocessed.time_start_ms,
                end_ms=preprocessed.time_end_ms,
                confidence=preprocessed.time_confidence,
                matched_spans=[s.matched_text for s in preprocessed.time_info.matched_spans],
            )
            if cfg.time_debug_mode:
                logger.info(
                    f"[TimeEnhance] Parsed time: {preprocessed.time_start_ms} - {preprocessed.time_end_ms}, conf={preprocessed.time_confidence:.2f}"
                )

        # Step 2: Vector search (time enhancement: expand candidate pool)
        effective_wide_search_top_k = cfg.wide_search_top_k
        if preprocessed.has_time and preprocessed.time_confidence >= cfg.time_conf_min:
            effective_wide_search_top_k = min(int(cfg.wide_search_top_k * cfg.time_wide_multiplier), cfg.time_wide_cap)
            if cfg.time_debug_mode:
                logger.info(
                    f"[TimeEnhance] Expanded wide_search_top_k: {cfg.wide_search_top_k} -> {effective_wide_search_top_k}"
                )

        node_distances, edge_distances = await _vector_search(
            preprocessed.vector_query, cfg, effective_wide_search_top_k
        )

        # Statistics for vector search results
        results_by_collection = {c: len(r) for c, r in node_distances.items()}
        total_hits = sum(results_by_collection.values())
        all_ids = {
            str(getattr(r, "id"))
            for results in node_distances.values()
            if results
            for r in results
            if getattr(r, "id", None)
        }
        rlog.log_vector_search(
            collections=cfg.collections,
            results_by_collection=results_by_collection,
            total_hits=total_hits,
            unique_ids=len(all_ids),
        )

        if not any(node_distances.values()):
            rlog.log_complete(0)
            return []

        # Step 2.5: Compute adaptive scoring context (before applying bonus, using raw scores)
        adaptive_context: AdaptiveScoringContext = None
        if cfg.enable_adaptive_weights:
            collection_stats = compute_collection_stats(node_distances, cfg, debug=cfg.adaptive_debug_mode)
            adaptive_context = compute_adaptive_context(collection_stats, cfg, debug=cfg.adaptive_debug_mode)
            if cfg.adaptive_debug_mode:
                logger.info(f"[AdaptiveScoring] {adaptive_context.debug_str()}")

        # Step 3: Apply exact match bonus
        bonus_stats = _apply_bonuses_with_stats(query, preprocessed, node_distances, cfg)
        rlog.log_bonus_apply(**bonus_stats)

        # Step 4: Two-phase projection
        best_by_id = compute_best_node_distances(node_distances)
        memory_fragment, projection_stats = await _two_phase_projection_with_stats(node_distances, best_by_id, cfg)

        # Log projection
        for phase_stat in projection_stats:
            rlog.log_graph_projection(**phase_stat)

        if not memory_fragment.edges:
            rlog.log_complete(0)
            return []

        # Step 5: Write back node distances
        _apply_node_distances(memory_fragment, best_by_id, cfg)

        # Step 6: Edge distance mapping
        await memory_fragment.map_vector_distances_to_graph_edges(edge_distances=edge_distances)

        # Step 7: Build relationship index
        index = build_relationship_index(memory_fragment)
        rlog.log_index_build(
            episodes=len(index.episode_ids),
            facets=len(index.facet_ids),
            points=len(index.point_ids),
            entities=len(index.entity_ids),
        )

        if not index.episode_ids:
            rlog.log_complete(0)
            return []

        # Step 8: Build edge_hit_map
        edge_hit_map = _build_edge_hit_map(edge_distances)

        # Step 9: Compute Bundle scoring
        bundles = compute_episode_bundles(index, best_by_id, edge_hit_map, cfg)

        if not bundles:
            rlog.log_complete(0)
            return []

        # Apply time bonus to bundles (before sorting)
        time_bonus_stats = None
        if preprocessed.has_time and preprocessed.time_confidence >= cfg.time_conf_min:
            time_bonus_stats = _apply_time_bonus_to_bundles(bundles, memory_fragment, preprocessed.time_info, cfg)
            if cfg.time_debug_mode and time_bonus_stats:
                logger.info(f"[TimeEnhance] Bundle time bonus: {time_bonus_stats}")
            rlog.log_time_bonus(bundles=len(bundles), **time_bonus_stats)

        # Step 10: Sort and take top-k
        top_bundles = heapq.nsmallest(cfg.top_k, bundles, key=lambda x: x.score)

        rlog.log_bundle_scoring(
            total_bundles=len(bundles),
            top_k=cfg.top_k,
            top_bundles=[{"episode_id": b.episode_id, "score": b.score, "path": b.best_path} for b in top_bundles[:5]],
        )

        TraceManager.event(
            "episodic.bundles.top",
            {
                "total": len(bundles),
                "top": [{"ep": b.episode_id[:20], "score": round(b.score, 4)} for b in top_bundles[:5]],
            },
        )

        # Step 11: Assemble output (pass time_info for edge sorting)
        facet_cost = _compute_facet_cost(index, best_by_id, edge_hit_map, cfg)
        out_edges = assemble_output_edges(
            top_bundles,
            index,
            best_by_id,
            facet_cost,
            edge_hit_map,
            cfg,
            adaptive_context=adaptive_context,
            time_info=preprocessed.time_info if preprocessed.has_time else None,
        )

        rlog.log_output_assemble(
            input_bundles=len(top_bundles),
            output_edges=len(out_edges),
            max_facets_per_ep=cfg.max_facets_per_episode,
            max_points_per_facet=cfg.max_points_per_facet,
        )

        TraceManager.event("episodic.search.done", {"n_edges": len(out_edges)})

        # Log completion
        rlog.log_complete(len(out_edges))

        return out_edges

    except Exception as e:
        rlog.log_error("episodic_bundle_search", e)
        raise


def _apply_overrides(
    cfg: EpisodicConfig,
    top_k,
    nodeset_name,
    wide_top_k,
    penalty,
    strict,
    max_ids,
    edge_miss,
    hop,
    max_facets,
    max_points,
    collections,
) -> EpisodicConfig:
    """Apply parameter overrides."""
    if top_k is not None:
        cfg.top_k = top_k
    if nodeset_name is not None:
        cfg.episodic_nodeset_name = nodeset_name
    if wide_top_k is not None:
        cfg.wide_search_top_k = wide_top_k
    if penalty is not None:
        cfg.triplet_distance_penalty = penalty
    if strict is not None:
        cfg.strict_nodeset_filtering = strict
    if max_ids is not None:
        cfg.max_relevant_ids = max_ids
    if edge_miss is not None:
        cfg.edge_miss_cost = edge_miss
    if hop is not None:
        cfg.hop_cost = hop
    if max_facets is not None:
        cfg.max_facets_per_episode = max_facets
    if max_points is not None:
        cfg.max_points_per_facet = max_points
    if collections is not None:
        cfg.collections = collections
    return cfg


async def _vector_search(
    query: str,
    cfg: EpisodicConfig,
    wide_search_top_k: Optional[int] = None,
) -> tuple:
    """Execute multi-collection vector search."""
    try:
        vector_engine = get_vector_provider()
    except Exception as e:
        logger.error(f"Failed to initialize vector engine: {e}")
        raise RuntimeError("Initialization error") from e

    query_vector = (await vector_engine.embedding_engine.embed_text([query]))[0]

    # Use provided wide_search_top_k, or fallback to config value
    limit = wide_search_top_k if wide_search_top_k is not None else cfg.wide_search_top_k

    async def search_in_collection(collection_name: str):
        try:
            return await vector_engine.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
            )
        except CollectionNotFoundError:
            return []

    results = await asyncio.gather(*[search_in_collection(c) for c in cfg.collections])

    node_distances = {c: r for c, r in zip(cfg.collections, results)}
    edge_distances = node_distances.get("RelationType_relationship_name", None)

    return node_distances, edge_distances


def _apply_bonuses(
    query: str,
    preprocessed: PreprocessedQuery,
    node_distances: Dict[str, list],
    cfg: EpisodicConfig,
) -> None:
    """Apply various match bonuses."""
    for collection_name, scored_results in node_distances.items():
        if collection_name == "RelationType_relationship_name":
            continue
        if not scored_results:
            continue

        # Keyword match bonus
        apply_keyword_match_bonus(preprocessed, scored_results, cfg)

        # Exact match bonus
        apply_exact_match_bonus(query, scored_results, cfg)


def _apply_bonuses_with_stats(
    query: str,
    preprocessed: PreprocessedQuery,
    node_distances: Dict[str, list],
    cfg: EpisodicConfig,
) -> Dict[str, int]:
    """Apply various match bonuses and return statistics."""
    import re

    stats = {
        "keyword_matches": 0,
        "exact_matches": 0,
        "number_matches": 0,
        "english_matches": 0,
    }

    # Pre-detect query features
    has_numbers = bool(re.search(r"\d", query))
    has_english = bool(re.search(r"[A-Za-z]", query))

    for collection_name, scored_results in node_distances.items():
        if collection_name == "RelationType_relationship_name":
            continue
        if not scored_results:
            continue

        # Record scores before bonus
        scores_before = {str(getattr(r, "id", "")): getattr(r, "score", 0) for r in scored_results}

        # Keyword match bonus
        apply_keyword_match_bonus(preprocessed, scored_results, cfg)

        # Exact match bonus
        apply_exact_match_bonus(query, scored_results, cfg)

        # Count results with changes
        for r in scored_results:
            rid = str(getattr(r, "id", ""))
            score_after = getattr(r, "score", 0)
            if rid in scores_before and score_after < scores_before[rid]:
                # Score decreased (distance reduced after bonus)
                if preprocessed.keyword and preprocessed.use_hybrid:
                    stats["keyword_matches"] += 1
                elif has_numbers:
                    stats["number_matches"] += 1
                elif has_english:
                    stats["english_matches"] += 1
                else:
                    stats["exact_matches"] += 1

    return stats


async def _two_phase_projection(
    node_distances: Dict[str, list],
    best_by_id: Dict[str, float],
    cfg: EpisodicConfig,
):
    """Two-phase graph projection."""
    # Collect relevant IDs
    all_hit_ids = {
        str(getattr(r, "id"))
        for collection_name, results in node_distances.items()
        if collection_name != "RelationType_relationship_name" and results
        for r in results
        if getattr(r, "id", None)
    }

    # Sort by score
    relevant_ids = sorted(all_hit_ids, key=lambda nid: best_by_id.get(nid, float("inf")))

    if cfg.max_relevant_ids and len(relevant_ids) > cfg.max_relevant_ids:
        relevant_ids = relevant_ids[: cfg.max_relevant_ids]

    if not relevant_ids:
        return await get_episodic_memory_fragment(config=cfg)

    # Step 1: Initial projection
    fragment_1 = await get_episodic_memory_fragment(
        relevant_ids_to_filter=relevant_ids,
        config=cfg,
    )

    # Step 2: Expand neighbors
    ids_1_set = set(relevant_ids)
    neighbor_ids = [nid for nid in fragment_1.nodes.keys() if nid not in ids_1_set]

    # Priority for neighbor node types (lower = higher priority)
    # Support both "Entity" (new) and "Entity" (legacy) type values
    TYPE_PRIO = {"Episode": 0, "Facet": 1, "FacetPoint": 2, "Entity": 3}

    def neighbor_sort_key(nid: str):
        n = fragment_1.nodes.get(nid)
        t = (n.attributes.get("type") if n else "") or ""
        return (TYPE_PRIO.get(t, 9), best_by_id.get(nid, float("inf")), nid)

    neighbor_ids.sort(key=neighbor_sort_key)

    max_expanded = cfg.max_relevant_ids * 2 if cfg.max_relevant_ids else None
    ids_2 = list(relevant_ids) + neighbor_ids
    if max_expanded and len(ids_2) > max_expanded:
        ids_2 = ids_2[:max_expanded]

    fragment_2 = await get_episodic_memory_fragment(
        relevant_ids_to_filter=ids_2,
        config=cfg,
    )

    return fragment_2 if fragment_2.edges else fragment_1


async def _two_phase_projection_with_stats(
    node_distances: Dict[str, list],
    best_by_id: Dict[str, float],
    cfg: EpisodicConfig,
):
    """Two-phase graph projection (with statistics)."""
    projection_stats = []

    # Collect relevant IDs
    all_hit_ids = {
        str(getattr(r, "id"))
        for collection_name, results in node_distances.items()
        if collection_name != "RelationType_relationship_name" and results
        for r in results
        if getattr(r, "id", None)
    }

    # Sort by score
    relevant_ids = sorted(all_hit_ids, key=lambda nid: best_by_id.get(nid, float("inf")))

    if cfg.max_relevant_ids and len(relevant_ids) > cfg.max_relevant_ids:
        relevant_ids = relevant_ids[: cfg.max_relevant_ids]

    if not relevant_ids:
        empty_fragment = await get_episodic_memory_fragment(config=cfg)
        projection_stats.append(
            {
                "phase": 1,
                "input_ids": 0,
                "projected_nodes": len(empty_fragment.nodes),
                "projected_edges": len(empty_fragment.edges),
            }
        )
        return empty_fragment, projection_stats

    # Step 1: Initial projection
    fragment_1 = await get_episodic_memory_fragment(
        relevant_ids_to_filter=relevant_ids,
        config=cfg,
    )

    projection_stats.append(
        {
            "phase": 1,
            "input_ids": len(relevant_ids),
            "projected_nodes": len(fragment_1.nodes),
            "projected_edges": len(fragment_1.edges),
        }
    )

    # Step 2: Expand neighbors
    ids_1_set = set(relevant_ids)
    neighbor_ids = [nid for nid in fragment_1.nodes.keys() if nid not in ids_1_set]

    # Priority for neighbor node types (lower = higher priority)
    # Support both "Entity" (new) and "Entity" (legacy) type values
    TYPE_PRIO = {"Episode": 0, "Facet": 1, "FacetPoint": 2, "Entity": 3}

    def neighbor_sort_key(nid: str):
        n = fragment_1.nodes.get(nid)
        t = (n.attributes.get("type") if n else "") or ""
        return (TYPE_PRIO.get(t, 9), best_by_id.get(nid, float("inf")), nid)

    neighbor_ids.sort(key=neighbor_sort_key)

    max_expanded = cfg.max_relevant_ids * 2 if cfg.max_relevant_ids else None
    ids_2 = list(relevant_ids) + neighbor_ids
    if max_expanded and len(ids_2) > max_expanded:
        ids_2 = ids_2[:max_expanded]

    fragment_2 = await get_episodic_memory_fragment(
        relevant_ids_to_filter=ids_2,
        config=cfg,
    )

    projection_stats.append(
        {
            "phase": 2,
            "input_ids": len(relevant_ids),
            "projected_nodes": len(fragment_2.nodes),
            "projected_edges": len(fragment_2.edges),
            "expanded_ids": len(ids_2),
        }
    )

    result = fragment_2 if fragment_2.edges else fragment_1
    return result, projection_stats


def _apply_node_distances(memory_fragment, best_by_id: Dict[str, float], cfg: EpisodicConfig) -> None:
    """Write back node distances."""
    for n in memory_fragment.nodes.values():
        nid = str(n.id)
        if nid in best_by_id:
            n.attributes["vector_distance"] = min(
                float(n.attributes.get("vector_distance", cfg.triplet_distance_penalty)),
                float(best_by_id[nid]),
            )


def _build_edge_hit_map(edge_distances) -> Dict[str, float]:
    """Build edge hit mapping."""
    edge_hit_map: Dict[str, float] = {}
    if edge_distances:
        for r in edge_distances:
            try:
                txt = r.payload.get("text")
                if txt:
                    txt_str = str(txt)
                    score = float(r.score)
                    prev = edge_hit_map.get(txt_str)
                    edge_hit_map[txt_str] = score if prev is None else min(prev, score)
            except Exception as e:
                logger.debug("Failed to process edge distance record: %s", e)
                continue
    return edge_hit_map


def _compute_facet_cost(
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    edge_hit_map: Dict[str, float],
    cfg: EpisodicConfig,
) -> Dict[str, float]:
    """Compute Facet cost (for output assembly)."""
    import math

    INF = float("inf")

    facet_cost: Dict[str, float] = {}

    for fid in index.facet_ids:
        best = best_by_id.get(fid, INF)

        for pid in index.points_by_facet.get(fid, set()):
            pd = best_by_id.get(pid, INF)
            if math.isinf(pd):
                continue
            eobj = index.facet_point_edge.get((fid, pid))
            if not eobj:
                continue
            key = eobj.attributes.get("edge_text") or eobj.attributes.get("relationship_name") or ""
            ec = float(edge_hit_map.get(key, cfg.edge_miss_cost)) if key else cfg.edge_miss_cost
            c = pd + ec + cfg.hop_cost
            if c < best:
                best = c

        facet_cost[fid] = best

    return facet_cost


def _apply_time_bonus_to_bundles(
    bundles: List,
    memory_fragment,
    time_info,
    cfg: EpisodicConfig,
) -> Dict[str, int]:
    """
    Apply time bonus to bundles.

    Strategy:
    - Check time fields of bundle's Episode and nodes on path
    - If matches query time range, reduce bundle score (lower score is better)

    Args:
        bundles: List of EpisodeBundle
        memory_fragment: MemoryGraph projected subgraph (contains nodes)
        time_info: QueryTimeInfo
        cfg: Configuration

    Returns:
        Statistics
    """
    from m_flow.retrieval.time.time_bonus import compute_time_match, TimeBonusConfig

    stats = {
        "matched": 0,
        "mentioned_time_matched": 0,
        "created_at_matched": 0,
        "avg_bonus": 0.0,
        "max_bonus": 0.0,
    }

    if not time_info or not time_info.has_time:
        return stats

    if not memory_fragment or not memory_fragment.nodes:
        return stats

    # Build time bonus configuration
    time_cfg = TimeBonusConfig(
        enabled=cfg.enable_time_bonus,
        bonus_max=cfg.time_bonus_bundle,
        score_floor=cfg.time_score_floor,
        query_conf_min=cfg.time_conf_min,
        mentioned_time_weight=cfg.time_mentioned_weight,
        created_at_weight=cfg.time_created_at_weight,
        # Mismatch penalty configuration
        enable_mismatch_penalty=cfg.enable_mismatch_penalty,
        mismatch_penalty_max=cfg.mismatch_penalty_max,
        mismatch_conf_threshold=cfg.mismatch_conf_threshold,
        mismatch_require_candidate_time=cfg.mismatch_require_candidate_time,
    )

    total_bonus = 0.0

    for bundle in bundles:
        # Get Episode node
        ep_node = memory_fragment.nodes.get(bundle.episode_id)
        if not ep_node:
            continue

        # Build payload dict from node attributes
        payload = ep_node.attributes

        # Compute time match
        time_bonus = compute_time_match({"payload": payload}, time_info, time_cfg)

        if time_bonus.bonus > 0:
            # Reduce score (lower score is better)
            bundle.score = max(time_cfg.score_floor, bundle.score - time_bonus.bonus)

            stats["matched"] += 1
            if time_bonus.match_type == "mentioned_time":
                stats["mentioned_time_matched"] += 1
            elif time_bonus.match_type == "created_at":
                stats["created_at_matched"] += 1

            total_bonus += time_bonus.bonus
            stats["max_bonus"] = max(stats["max_bonus"], time_bonus.bonus)

        # Handle mismatch penalty
        elif time_bonus.penalty > 0:
            # Increase score (lower score is better, penalty makes it worse)
            bundle.score = bundle.score + time_bonus.penalty
            stats["penalized"] = stats.get("penalized", 0) + 1

    if stats["matched"] > 0:
        stats["avg_bonus"] = total_bonus / stats["matched"]

    return stats
