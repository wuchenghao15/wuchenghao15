"""
Output assembly module.

Responsibilities:
- Assemble output edges from top Bundles
- Edge deduplication and sorting
- Adaptive scoring sorting
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge
from m_flow.shared.logging_utils import get_logger

from .config import EpisodicConfig
from .bundle_scorer import EpisodeBundle, RelationshipIndex, get_edge_relationship
from .adaptive_scoring import (
    AdaptiveScoringContext,
    compute_lambda,
    compute_semantic_score,
    compute_final_score,
    get_exact_match_bonus,
)

logger = get_logger(__name__)


def assemble_output_edges(
    bundles: List[EpisodeBundle],
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    facet_cost: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
    adaptive_context: Optional[AdaptiveScoringContext] = None,
    time_info=None,  # QueryTimeInfo for time enhancement
) -> List[Edge]:
    """
    Assemble output edges from top Bundles.

    Supports two display modes via config.display_mode:
      - "detail":  Facet + Entity edges (no Episode summary node, no FacetPoint)
      - "summary": Episode summary only (no Facet/FacetPoint/Entity)

    Args:
        bundles: Sorted top-k Bundles
        index: Relationship index
        best_by_id: Node vector distances
        facet_cost: Facet path costs
        edge_hit_map: Edge vector distances
        config: Configuration
        adaptive_context: Adaptive scoring context
        time_info: Query time parsing result

    Returns:
        List[Edge]: Sorted output edges
    """
    mode = getattr(config, "display_mode", "detail")

    if mode == "summary":
        return _assemble_summary_mode(bundles, index, config)

    if mode == "highly_related_summary":
        return _assemble_highly_related_summary_mode(
            bundles,
            index,
            best_by_id,
            facet_cost,
            edge_hit_map,
            config,
        )

    return _assemble_detail_mode(
        bundles,
        index,
        best_by_id,
        facet_cost,
        edge_hit_map,
        config,
        adaptive_context=adaptive_context,
        time_info=time_info,
    )


def _assemble_summary_mode(
    bundles: List[EpisodeBundle],
    index: RelationshipIndex,
    config: EpisodicConfig,
) -> List[Edge]:
    """
    Summary mode: output only Episode nodes as synthetic self-referencing edges.

    Creates a lightweight edge per Episode carrying the summary text,
    so downstream resolve_edges_to_text can render it.
    """
    from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import (
        Edge as EdgeCls,
    )

    out_edges: List[Edge] = []

    for b in bundles:
        ep = b.episode_id

        # Find the Episode node from any edge in the index
        ep_node = None
        for fid in index.facets_by_episode.get(ep, set()):
            edge = index.ep_facet_edge.get((ep, fid))
            if edge:
                n1_type = edge.node1.attributes.get("type", "")
                if n1_type == "Episode" and str(edge.node1.id) == ep:
                    ep_node = edge.node1
                elif edge.node2.attributes.get("type", "") == "Episode" and str(edge.node2.id) == ep:
                    ep_node = edge.node2
                if ep_node:
                    break

        if not ep_node:
            # Try entity edges
            for en in index.entities_by_episode.get(ep, set()):
                edge = index.ep_entity_edge.get((ep, en))
                if edge:
                    if edge.node1.attributes.get("type") == "Episode" and str(edge.node1.id) == ep:
                        ep_node = edge.node1
                    elif edge.node2.attributes.get("type") == "Episode" and str(edge.node2.id) == ep:
                        ep_node = edge.node2
                    if ep_node:
                        break

        if not ep_node:
            continue

        # Create a summary-only edge: Episode → Episode (self-link carrying summary)
        summary_text = ep_node.attributes.get("summary", "")
        summary_edge = EdgeCls(
            node1=ep_node,
            node2=ep_node,
            attributes={
                "relationship_name": "episode_summary",
                "edge_text": summary_text,
            },
        )
        out_edges.append(summary_edge)

    return out_edges


def _assemble_highly_related_summary_mode(
    bundles: List[EpisodeBundle],
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    facet_cost: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
) -> List[Edge]:
    """
    Highly-related summary mode: output Episode summary sections
    filtered to only those whose Facets were retrieved.

    For each Episode in the top bundles:
    1. Determine which Facets were selected (top scoring Facets)
    2. Parse Episode.summary into 【title】content sections
    3. Keep only sections whose title matches a selected Facet name
    4. Emit a synthetic edge carrying the filtered summary

    This provides focused, noise-free context to the LLM.
    """
    from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import (
        Edge as EdgeCls,
    )

    out_edges: List[Edge] = []

    for b in bundles:
        ep = b.episode_id

        # 1. Find the Episode node
        ep_node = _find_episode_node(ep, index)
        if not ep_node:
            continue

        full_summary = ep_node.attributes.get("summary", "")
        if not full_summary:
            continue

        # 2. Get the top matched Facet names for this Episode
        matched_facet_names = set()

        # Add best-path facet
        if b.best_facet_id:
            ef = index.ep_facet_edge.get((ep, b.best_facet_id))
            if ef:
                for node in (ef.node1, ef.node2):
                    if node.attributes.get("type") == "Facet":
                        fname = node.attributes.get("name", "")
                        if fname:
                            matched_facet_names.add(fname)

        # Add top-k facets from scoring
        facet_candidates = _get_top_facets(ep, index, facet_cost, edge_hit_map, config)
        for _, fid in facet_candidates:
            ef = index.ep_facet_edge.get((ep, fid))
            if ef:
                for node in (ef.node1, ef.node2):
                    if node.attributes.get("type") == "Facet":
                        fname = node.attributes.get("name", "")
                        if fname:
                            matched_facet_names.add(fname)

        # 3. Parse summary sections and filter
        filtered_summary = _filter_summary_sections(full_summary, matched_facet_names)

        if not filtered_summary:
            # Fallback: use full summary if no sections matched
            filtered_summary = full_summary

        # 4. Emit synthetic edge
        summary_edge = EdgeCls(
            node1=ep_node,
            node2=ep_node,
            attributes={
                "relationship_name": "episode_summary",
                "edge_text": filtered_summary,
            },
        )
        out_edges.append(summary_edge)

    return out_edges


def _find_episode_node(ep_id: str, index: RelationshipIndex):
    """Find the Episode node object from the index."""
    for fid in index.facets_by_episode.get(ep_id, set()):
        edge = index.ep_facet_edge.get((ep_id, fid))
        if edge:
            if edge.node1.attributes.get("type") == "Episode" and str(edge.node1.id) == ep_id:
                return edge.node1
            if edge.node2.attributes.get("type") == "Episode" and str(edge.node2.id) == ep_id:
                return edge.node2
    for en in index.entities_by_episode.get(ep_id, set()):
        edge = index.ep_entity_edge.get((ep_id, en))
        if edge:
            if edge.node1.attributes.get("type") == "Episode" and str(edge.node1.id) == ep_id:
                return edge.node1
            if edge.node2.attributes.get("type") == "Episode" and str(edge.node2.id) == ep_id:
                return edge.node2
    return None


def _filter_summary_sections(
    full_summary: str,
    matched_facet_names: Set[str],
) -> str:
    """
    Parse Episode summary into 【title】content sections,
    keep only sections whose title matches a retrieved Facet name.

    Summary format: 【Title A】Content A 【Title B】Content B ...

    Matching is case-insensitive and strips whitespace.
    """
    import re

    if not matched_facet_names:
        return full_summary

    # Normalize facet names for matching
    normalized_names = {name.strip().lower() for name in matched_facet_names}

    # Split summary into sections by 【...】 markers
    # Pattern: capture title inside 【】 and content until next 【 or end
    pattern = r"【([^】]+)】"
    splits = re.split(pattern, full_summary)

    # splits = [before_first_marker, title1, content1, title2, content2, ...]
    # If summary doesn't use 【】 format, return as-is
    if len(splits) < 3:
        return full_summary

    kept_sections = []
    i = 1  # Start after any text before first marker
    while i < len(splits) - 1:
        title = splits[i].strip()
        content = splits[i + 1].strip() if i + 1 < len(splits) else ""

        if title.lower() in normalized_names:
            kept_sections.append(f"【{title}】{content}")

        i += 2

    if not kept_sections:
        return full_summary

    return " ".join(kept_sections)


def _assemble_detail_mode(
    bundles: List[EpisodeBundle],
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    facet_cost: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
    adaptive_context: Optional[AdaptiveScoringContext] = None,
    time_info=None,
) -> List[Edge]:
    """
    Detail mode: output Facet + Entity edges.

    Skips Episode summary (Episode only appears as parent in edges)
    and FacetPoint (too granular for overview display).
    Only outputs Episode→Facet and Episode→Entity edges.
    """
    out_edges: List[Edge] = []
    out_seen: Set[Tuple[frozenset, str]] = set()

    def push_edge(e: Edge) -> None:
        rel = get_edge_relationship(e)
        k = (frozenset({str(e.node1.id), str(e.node2.id)}), rel)
        if k in out_seen:
            return
        out_seen.add(k)
        out_edges.append(e)

    for b in bundles:
        ep = b.episode_id

        # Output best-path Facet edge (skip FacetPoint)
        if b.best_facet_id:
            ef = index.ep_facet_edge.get((ep, b.best_facet_id))
            if ef:
                push_edge(ef)

        # Output best-path Entity edge
        if b.best_entity_id:
            # Try Episode → Entity first
            ee = index.ep_entity_edge.get((ep, b.best_entity_id))
            if ee:
                push_edge(ee)
            # Also try Facet → Entity if path is facet_entity
            if b.best_path == "facet_entity" and b.best_facet_id:
                fe = index.facet_entity_edge.get((b.best_facet_id, b.best_entity_id))
                if fe:
                    push_edge(fe)

        # Output top Facets (no FacetPoints)
        facet_candidates = _get_top_facets(ep, index, facet_cost, edge_hit_map, config)

        if not facet_candidates:
            fallback_fids = list(index.facets_by_episode.get(ep, set()))
            fallback_fids.sort(key=lambda fid: best_by_id.get(fid, float("inf")))
            fallback_fids = fallback_fids[: config.max_facets_per_episode]
            for fid in fallback_fids:
                ef = index.ep_facet_edge.get((ep, fid))
                if ef:
                    push_edge(ef)

        for _, fid in facet_candidates:
            ef = index.ep_facet_edge.get((ep, fid))
            if ef:
                push_edge(ef)
            # Detail mode: skip FacetPoint edges

        # Output top Concepts (from both Episode→Entity and Facet→Entity)
        entity_candidates = _get_top_entities(ep, index, best_by_id, edge_hit_map, config)
        for _, en in entity_candidates:
            # Try Episode → Entity first
            ee = index.ep_entity_edge.get((ep, en))
            if ee:
                push_edge(ee)
            else:
                # Fallback: try Facet → Entity edges
                # Find which Facet connects to this Entity
                for fid in index.facets_by_episode.get(ep, set()):
                    fe = index.facet_entity_edge.get((fid, en))
                    if fe:
                        push_edge(fe)
                        break  # Only need one edge per Entity

    # Sort
    _sort_output_edges(
        out_edges,
        bundles,
        index,
        best_by_id,
        facet_cost,
        edge_hit_map,
        config,
        adaptive_context=adaptive_context,
        time_info=time_info,
    )

    return out_edges


def _get_top_facets(
    ep: str,
    index: RelationshipIndex,
    facet_cost: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
) -> List[Tuple[float, str]]:
    """Get top facets under an Episode."""
    INF = float("inf")
    candidates: List[Tuple[float, str]] = []

    for fid in index.facets_by_episode.get(ep, set()):
        fc = facet_cost.get(fid, INF)
        eobj = index.ep_facet_edge.get((ep, fid))
        if not eobj:
            continue
        key = _get_edge_key_for_embedding(eobj)
        ec = float(edge_hit_map.get(key, config.edge_miss_cost)) if key else config.edge_miss_cost
        c = fc + ec + config.hop_cost
        candidates.append((c, fid))

    candidates.sort(key=lambda x: x[0])

    if config.max_facets_per_episode:
        candidates = candidates[: config.max_facets_per_episode]

    return candidates


def _get_top_points(
    fid: str,
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
) -> List[Tuple[float, str]]:
    """Get top points under a Facet."""
    INF = float("inf")
    candidates: List[Tuple[float, str]] = []

    for pid in index.points_by_facet.get(fid, set()):
        pd = best_by_id.get(pid, INF)
        if math.isinf(pd):
            continue
        eobj = index.facet_point_edge.get((fid, pid))
        if not eobj:
            continue
        key = _get_edge_key_for_embedding(eobj)
        ec = float(edge_hit_map.get(key, config.edge_miss_cost)) if key else config.edge_miss_cost
        c = pd + ec + config.hop_cost
        candidates.append((c, pid))

    candidates.sort(key=lambda x: x[0])

    if config.max_points_per_facet:
        candidates = candidates[: config.max_points_per_facet]

    return candidates


def _get_top_entities(
    ep: str,
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
) -> List[Tuple[float, str]]:
    """Get top entities under an Episode (including Facet→Entity)."""
    INF = float("inf")
    candidates: List[Tuple[float, str]] = []
    seen_entities: set = set()

    # Direct Episode → Entity
    for en in index.entities_by_episode.get(ep, set()):
        ed = best_by_id.get(en, INF)
        if math.isinf(ed):
            continue
        eobj = index.ep_entity_edge.get((ep, en))
        if not eobj:
            continue
        key = _get_edge_key_for_embedding(eobj)
        ec = float(edge_hit_map.get(key, config.edge_miss_cost)) if key else config.edge_miss_cost
        c = ed + ec + config.hop_cost
        candidates.append((c, en))
        seen_entities.add(en)

    # Also include Facet → Entity (for entities reachable via facets)
    for fid in index.facets_by_episode.get(ep, set()):
        for en in index.entities_by_facet.get(fid, set()):
            if en in seen_entities:
                continue  # Avoid duplicates
            ed = best_by_id.get(en, INF)
            if math.isinf(ed):
                continue
            eobj = index.facet_entity_edge.get((fid, en))
            if not eobj:
                continue
            key = _get_edge_key_for_embedding(eobj)
            ec = float(edge_hit_map.get(key, config.edge_miss_cost)) if key else config.edge_miss_cost
            # 2 hops: Entity → Facet → Episode
            c = ed + ec + config.hop_cost * 2
            candidates.append((c, en))
            seen_entities.add(en)

    candidates.sort(key=lambda x: x[0])
    return candidates[:2]  # Only take 2 entities


def _sort_output_edges(
    out_edges: List[Edge],
    bundles: List[EpisodeBundle],
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    facet_cost: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
    adaptive_context: Optional[AdaptiveScoringContext] = None,
    time_info=None,  # Time enhancement
) -> None:
    """Sort output edges in-place.

    If enable_adaptive_weights=True and adaptive_context exists, use adaptive scoring:
      final = lambda x semantic + (1-lambda) x struct - time_bonus

    Otherwise use traditional sort keys (by priority):
    1. Episode rank - from bundle ranking
    2. Node cost - from best_by_id and facet_cost
    3. Edge vector cost - from edge_hit_map
    4. Edge type priority - has_point > has_facet > involves_entity
    5. Node ID - for stable sorting
    """
    episode_rank = {b.episode_id: i for i, b in enumerate(bundles)}
    episode_bundle_cost = {b.episode_id: b.score for b in bundles}

    # Facet -> Episode mapping
    facet_to_episode: Dict[str, str] = {}
    for ep, fset in index.facets_by_episode.items():
        for fid in fset:
            facet_to_episode[fid] = ep

    # Use adaptive scoring or traditional sorting
    use_adaptive = config.enable_adaptive_weights and adaptive_context is not None

    if use_adaptive:
        _sort_output_edges_adaptive(
            out_edges,
            bundles,
            index,
            best_by_id,
            facet_cost,
            edge_hit_map,
            config,
            adaptive_context,
            episode_rank,
            facet_to_episode,
            time_info=time_info,
        )
    else:
        _sort_output_edges_basic(
            out_edges,
            bundles,
            index,
            best_by_id,
            facet_cost,
            edge_hit_map,
            config,
            episode_rank,
            episode_bundle_cost,
            facet_to_episode,
            time_info=time_info,
        )


def _sort_output_edges_basic(
    out_edges: List[Edge],
    bundles: List[EpisodeBundle],
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    facet_cost: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
    episode_rank: Dict[str, int],
    episode_bundle_cost: Dict[str, float],
    facet_to_episode: Dict[str, str],
    time_info=None,  # Time enhancement
) -> None:
    """Traditional sorting logic (kept as fallback)."""
    EDGE_TYPE_ORDER = {"has_point": 1, "has_facet": 2, "involves_entity": 3}

    # Pre-compute time bonuses
    time_bonuses: Dict[str, EdgeTimeScore] = {}
    if time_info and time_info.has_time and config.enable_time_bonus:
        time_bonuses = _compute_edge_time_bonuses(out_edges, index, time_info, config)

    def get_sort_key(edge: Edge) -> Tuple[int, float, float, int, str]:
        # Episode rank
        ep_id = _get_edge_episode_id(edge, facet_to_episode)
        ep_rank = episode_rank.get(ep_id, 10**9)

        # Node cost
        n1_id = str(edge.node1.id)
        n2_id = str(edge.node2.id)
        n1_cost = _get_node_cost(
            n1_id,
            edge.node1.attributes.get("type", ""),
            best_by_id,
            facet_cost,
            episode_bundle_cost,
        )
        n2_cost = _get_node_cost(
            n2_id,
            edge.node2.attributes.get("type", ""),
            best_by_id,
            facet_cost,
            episode_bundle_cost,
        )
        best_node_cost = min(n1_cost, n2_cost)

        # Apply time bonus/penalty
        edge_key = f"{n1_id}:{n2_id}"
        time_score = time_bonuses.get(edge_key)
        if time_score:
            # Apply net effect: bonus reduces score (good), penalty increases score (bad)
            best_node_cost = max(config.time_score_floor, best_node_cost - time_score.net_effect)

        # Edge vector cost
        emb_key = _get_edge_key_for_embedding(edge)
        edge_vector_cost = float(edge_hit_map.get(emb_key, config.edge_miss_cost)) if emb_key else config.edge_miss_cost

        # Edge type priority
        rel = get_edge_relationship(edge)
        edge_priority = EDGE_TYPE_ORDER.get(rel, 4)

        return (ep_rank, best_node_cost, edge_vector_cost, edge_priority, n1_id)

    out_edges.sort(key=get_sort_key)


def _sort_output_edges_adaptive(
    out_edges: List[Edge],
    bundles: List[EpisodeBundle],
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    facet_cost: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
    adaptive_context: AdaptiveScoringContext,
    episode_rank: Dict[str, int],
    facet_to_episode: Dict[str, str],
    time_info=None,  # Time enhancement
) -> None:
    """Adaptive scoring sort logic.

    Uses formula: final = lambda x semantic + (1-lambda) x struct - time_bonus

    Where:
    - semantic = W_node x node_score + W_edge x edge_score
    - struct = 1 - 1/(1 + ep_rank x decay)
    - lambda is dynamically computed from confidence, exact match, etc.
    - time_bonus: Time enhancement bonus
    """
    EDGE_TYPE_ORDER = {"has_point": 1, "has_facet": 2, "involves_entity": 3}

    # Pre-compute time bonuses
    time_bonuses: Dict[str, EdgeTimeScore] = {}
    if time_info and time_info.has_time and config.enable_time_bonus:
        time_bonuses = _compute_edge_time_bonuses(out_edges, index, time_info, config)

    def get_adaptive_sort_key(edge: Edge) -> Tuple[float, int, str]:
        # Get node information
        n1_id = str(edge.node1.id)
        n2_id = str(edge.node2.id)
        n1_cost = best_by_id.get(n1_id, config.triplet_distance_penalty)
        n2_cost = best_by_id.get(n2_id, config.triplet_distance_penalty)
        node_score = min(n1_cost, n2_cost)

        # Get edge vector score
        emb_key = _get_edge_key_for_embedding(edge)
        edge_score = float(edge_hit_map.get(emb_key, config.edge_miss_cost)) if emb_key else config.edge_miss_cost

        # Compute semantic score
        semantic = compute_semantic_score(node_score, edge_score, adaptive_context.w_node, adaptive_context.w_edge)

        # Get Episode rank
        ep_id = _get_edge_episode_id(edge, facet_to_episode)
        ep_rank = episode_rank.get(ep_id, len(bundles))

        # Estimate exact match bonus
        exact_match = get_exact_match_bonus(node_score, edge_score)

        # Compute lambda
        lambda_val = compute_lambda(
            adaptive_context.conf_node,
            adaptive_context.conf_edge,
            exact_match,
            adaptive_context.best_gap,
            semantic,
            config,
        )

        # Compute final score
        final = compute_final_score(semantic, ep_rank, lambda_val, config)

        # Apply time bonus/penalty
        edge_key = f"{n1_id}:{n2_id}"
        time_score = time_bonuses.get(edge_key)
        if time_score:
            # Apply net effect: bonus reduces score (good), penalty increases score (bad)
            final = max(config.time_score_floor, final - time_score.net_effect)

        # Edge type priority as tiebreaker
        rel = get_edge_relationship(edge)
        edge_priority = EDGE_TYPE_ORDER.get(rel, 4)

        return (final, edge_priority, n1_id)

    # Debug logging
    if config.adaptive_debug_mode:
        logger.info("[AdaptiveSort] Sorting edges with adaptive scoring...")
        for i, e in enumerate(out_edges[:5]):
            key = get_adaptive_sort_key(e)
            logger.info(f"  Edge {i}: final={key[0]:.4f}, priority={key[1]}, rel={get_edge_relationship(e)}")

    out_edges.sort(key=get_adaptive_sort_key)


def _get_edge_episode_id(edge: Edge, facet_to_episode: Dict[str, str]) -> str:
    """Get the Episode ID that the edge belongs to."""
    t1 = edge.node1.attributes.get("type", "")
    t2 = edge.node2.attributes.get("type", "")

    if t1 == "Episode":
        return str(edge.node1.id)
    if t2 == "Episode":
        return str(edge.node2.id)

    rel = get_edge_relationship(edge)

    # Handle edges involving Facet (has_point, involves_entity)
    if rel == "has_point":
        fid = str(edge.node1.id) if t1 == "Facet" else str(edge.node2.id)
        return facet_to_episode.get(fid, "")

    # Handle Facet → Entity (involves_entity where Facet is involved)
    if rel == "involves_entity":
        if t1 == "Facet":
            return facet_to_episode.get(str(edge.node1.id), "")
        if t2 == "Facet":
            return facet_to_episode.get(str(edge.node2.id), "")

    return ""


def _get_node_cost(
    node_id: str,
    node_type: str,
    best_by_id: Dict[str, float],
    facet_cost: Dict[str, float],
    episode_cost: Dict[str, float],
) -> float:
    """Get node path cost."""
    if node_type == "Facet":
        cost = facet_cost.get(node_id)
        if cost is not None and not math.isinf(cost):
            return cost
    elif node_type == "Episode":
        cost = episode_cost.get(node_id)
        if cost is not None and not math.isinf(cost):
            return cost

    cost = best_by_id.get(node_id)
    if cost is not None and not math.isinf(cost):
        return cost

    return 1.5  # Default value


def _get_edge_key_for_embedding(edge: Edge) -> str:
    """Get edge embedding key."""
    return (
        edge.attributes.get("edge_text")
        or edge.attributes.get("relationship_type")
        or edge.attributes.get("relationship_name")
        or ""
    )


@dataclass
class EdgeTimeScore:
    """Edge time score (includes bonus and penalty)."""

    bonus: float = 0.0  # Positive bonus (reduces score = improves ranking)
    penalty: float = 0.0  # Negative penalty (increases score = lowers ranking)

    @property
    def net_effect(self) -> float:
        """Net effect (bonus - penalty) for adjusting score."""
        return self.bonus - self.penalty


def _compute_edge_time_bonuses(
    edges: List[Edge],
    index,
    time_info,
    config: EpisodicConfig,
) -> Dict[str, EdgeTimeScore]:
    """
    Pre-compute time bonuses and penalties for each edge.

    Returns: Mapping of {"{node1_id}:{node2_id}": EdgeTimeScore}
    """
    from m_flow.retrieval.time.time_bonus import compute_time_match, TimeBonusConfig

    result: Dict[str, EdgeTimeScore] = {}

    if not time_info or not time_info.has_time:
        return result

    # Build time bonus configuration
    time_cfg = TimeBonusConfig(
        enabled=config.enable_time_bonus,
        bonus_max=config.time_bonus_max,
        score_floor=config.time_score_floor,
        query_conf_min=config.time_conf_min,
        mentioned_time_weight=config.time_mentioned_weight,
        created_at_weight=config.time_created_at_weight,
        # Mismatch penalty configuration
        enable_mismatch_penalty=config.enable_mismatch_penalty,
        mismatch_penalty_max=config.mismatch_penalty_max,
        mismatch_conf_threshold=config.mismatch_conf_threshold,
        mismatch_require_candidate_time=config.mismatch_require_candidate_time,
    )

    for edge in edges:
        n1_id = str(edge.node1.id)
        n2_id = str(edge.node2.id)
        edge_key = f"{n1_id}:{n2_id}"

        # Get time attributes from both endpoints
        n1_attrs = edge.node1.attributes
        n2_attrs = edge.node2.attributes

        # Compute time match for both nodes, take higher value
        bonus1 = compute_time_match({"payload": n1_attrs}, time_info, time_cfg)
        bonus2 = compute_time_match({"payload": n2_attrs}, time_info, time_cfg)

        best_bonus = max(bonus1.bonus, bonus2.bonus)
        # Penalty takes smaller value (if both nodes have penalty, choose lighter one)
        min_penalty = min(bonus1.penalty, bonus2.penalty)

        if best_bonus > 0 or min_penalty > 0:
            result[edge_key] = EdgeTimeScore(bonus=best_bonus, penalty=min_penalty)

    return result
