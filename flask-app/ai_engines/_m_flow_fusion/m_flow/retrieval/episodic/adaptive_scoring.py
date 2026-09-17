"""
Adaptive Scoring Module - Core adaptive scoring logic.

Implements a confidence-based adaptive scoring system using raw vector search distances,
dynamically adjusting the weights between semantic signals and structural signals.

Core formulas:
- Conf = f_dist(raw_distance / baseline) x f_gap(gap)
- semantic = W_node x node_score + W_edge x edge_score
- final = lambda x semantic + (1-lambda) x struct
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from m_flow.shared.logging_utils import get_logger

logger = get_logger(__name__)


# ============================================================
# Data class definitions
# ============================================================


@dataclass
class CollectionStats:
    """Statistics for a single vector collection."""

    collection_name: str
    top1_raw_distance: float
    top2_raw_distance: Optional[float]
    gap: float
    baseline: float
    ratio: float
    confidence: float
    collection_type: str  # 'node' or 'edge'

    def debug_str(self) -> str:
        """Return debug string representation."""
        return (
            f"CollectionStats({self.collection_name}: "
            f"raw={self.top1_raw_distance:.4f}, gap={self.gap:.4f}, "
            f"ratio={self.ratio:.2f}, conf={self.confidence:.3f}, "
            f"type={self.collection_type})"
        )


@dataclass
class AdaptiveScoringContext:
    """Adaptive scoring context - query-level scoring parameters."""

    collection_stats: Dict[str, CollectionStats]
    conf_node: float
    conf_edge: float
    w_node: float
    w_edge: float
    best_gap: float
    best_node_source: Optional[str] = None
    best_edge_source: Optional[str] = None

    def debug_str(self) -> str:
        """Return debug string representation."""
        return (
            f"AdaptiveScoringContext(conf_node={self.conf_node:.3f}, "
            f"conf_edge={self.conf_edge:.3f}, w_node={self.w_node:.3f}, "
            f"w_edge={self.w_edge:.3f}, best_gap={self.best_gap:.4f})"
        )


# ============================================================
# Core functions: f_dist, f_gap, compute_confidence
# ============================================================


def f_dist(ratio: float, config: Any) -> float:
    """
    Distance factor - evaluate raw distance quality relative to baseline.

    Args:
        ratio: raw_distance / baseline
        config: EpisodicConfig object.

    Returns:
        float: Quality factor in [0.1, 1.0], higher means better match.

    Mapping:
        ratio < 0.5  -> 1.0 (very good)
        ratio = 0.75 -> 0.75 (good)
        ratio = 1.0  -> 0.5 (average)
        ratio = 1.5  -> 0.3 (poor)
        ratio > 1.5  -> approaches 0.1 (very poor)
    """
    if ratio < config.ratio_good:  # 0.5
        return 1.0
    elif ratio < config.ratio_avg:  # 1.0
        # Linear decay from 1.0 to 0.5
        return 1.0 - (ratio - config.ratio_good) / (config.ratio_avg - config.ratio_good) * 0.5
    elif ratio < config.ratio_poor:  # 1.5
        # Linear decay from 0.5 to 0.3
        return 0.5 - (ratio - config.ratio_avg) / (config.ratio_poor - config.ratio_avg) * 0.2
    else:
        # Continue decay from 0.3, minimum 0.1
        return max(0.1, 0.3 - (ratio - config.ratio_poor) * 0.2)


def f_gap(gap: float, config: Any) -> float:
    """
    Gap factor - evaluate the distance gap between Top-1 and Top-2.

    Args:
        gap: max(0, top2_raw - top1_raw)
        config: EpisodicConfig object.

    Returns:
        float: Discriminability factor in [0.2, 1.0], higher means Top-1 is more significant.

    Mapping:
        gap <= 0.01 -> 0.2 (indistinguishable)
        gap = 0.03  -> 0.4 (slight distinction)
        gap = 0.05  -> 0.6 (moderate distinction)
        gap = 0.10  -> 0.8 (clear distinction)
        gap >= 0.15 -> 1.0 (very significant)
    """
    if gap > config.gap_high:  # 0.15
        return 1.0
    elif gap > config.gap_low:  # 0.05
        # Linear increase from 0.6 to 1.0
        return 0.6 + (gap - config.gap_low) / (config.gap_high - config.gap_low) * 0.4
    elif gap > config.gap_trivial:  # 0.01
        # Linear increase from 0.2 to 0.6
        return 0.2 + (gap - config.gap_trivial) / (config.gap_low - config.gap_trivial) * 0.4
    else:
        return 0.2


def compute_confidence(raw_distance: float, baseline: float, gap: float, config: Any) -> Tuple[float, float]:
    """
    Compute confidence for a single collection.

    Args:
        raw_distance: Raw vector distance.
        baseline: Baseline distance for this collection.
        gap: Distance gap between Top-1 and Top-2.
        config: EpisodicConfig object.

    Returns:
        Tuple[float, float]: (confidence, ratio)
    """
    ratio = raw_distance / baseline if baseline > 0 else 1.0
    dist_factor = f_dist(ratio, config)
    gap_factor = f_gap(gap, config)
    confidence = dist_factor * gap_factor

    # Debug assertion
    assert 0 <= confidence <= 1, f"confidence out of range: {confidence}"

    return confidence, ratio


# ============================================================
# Aggregation: compute_collection_stats, compute_adaptive_context
# ============================================================


def compute_collection_stats(
    search_results: Dict[str, List], config: Any, debug: bool = False
) -> Dict[str, CollectionStats]:
    """
    Compute statistics for each collection.

    Args:
        search_results: Vector search results {collection_name: [VectorSearchHit, ...]}.
        config: EpisodicConfig object.
        debug: Whether to output debug info.

    Returns:
        Dict[str, CollectionStats]: Statistics per collection.
    """
    stats = {}

    for coll_name, results in search_results.items():
        if not results:
            if debug:
                logger.debug(f"[CollectionStats] {coll_name}: no results, skipped")
            continue

        # Get baseline
        baseline = config.get_baseline(coll_name)

        # Get Top-1 raw distance
        top1_raw = getattr(results[0], "raw_distance", None)

        if top1_raw is None:
            # Use baseline as fallback when raw_distance is unavailable
            top1_raw = baseline
            if debug:
                logger.warning(
                    f"[CollectionStats] {coll_name}: raw_distance is None, "
                    f"using baseline={baseline} as fallback (conservative)"
                )

        # Get Top-2 raw distance and compute gap
        if len(results) >= 2:
            top2_raw = getattr(results[1], "raw_distance", None)
            if top2_raw is None:
                # Use baseline-based fallback for Top-2
                top2_raw = baseline * 1.1
            gap = max(0.0, top2_raw - top1_raw)  # Ensure gap is non-negative
        else:
            top2_raw = None
            gap = 0.0

        # Compute confidence
        confidence, ratio = compute_confidence(top1_raw, baseline, gap, config)

        # Determine collection type
        # Check edge collections first to avoid false matches with node collections
        is_edge = "relationship" in coll_name.lower() or "edge" in coll_name.lower()
        is_node = not is_edge and (
            "search_text" in coll_name or "anchor_text" in coll_name or "name" in coll_name or "summary" in coll_name
        )

        # Final type: edge collection takes priority, then check node features, default to edge
        if is_edge:
            coll_type = "edge"
        elif is_node:
            coll_type = "node"
        else:
            coll_type = "edge"  # Default to edge type

        stats[coll_name] = CollectionStats(
            collection_name=coll_name,
            top1_raw_distance=top1_raw,
            top2_raw_distance=top2_raw,
            gap=gap,
            baseline=baseline,
            ratio=ratio,
            confidence=confidence,
            collection_type=coll_type,
        )

        if debug:
            logger.debug(f"[CollectionStats] {stats[coll_name].debug_str()}")

    return stats


def compute_adaptive_context(
    collection_stats: Dict[str, CollectionStats], config: Any, debug: bool = False
) -> AdaptiveScoringContext:
    """
    Compute adaptive scoring context.

    Args:
        collection_stats: Statistics per collection.
        config: EpisodicConfig object.
        debug: Whether to output debug info.

    Returns:
        AdaptiveScoringContext: Query-level scoring context.
    """
    # Categorize confidences by type
    node_stats = [(k, v) for k, v in collection_stats.items() if v.collection_type == "node"]
    edge_stats = [(k, v) for k, v in collection_stats.items() if v.collection_type == "edge"]

    # Take the highest confidence per type (capture strongest signal)
    if node_stats:
        best_node = max(node_stats, key=lambda x: x[1].confidence)
        conf_node = best_node[1].confidence
        best_node_source = best_node[0]
    else:
        conf_node = 0.5  # Default medium confidence
        best_node_source = None

    if edge_stats:
        best_edge = max(edge_stats, key=lambda x: x[1].confidence)
        conf_edge = best_edge[1].confidence
        best_edge_source = best_edge[0]
    else:
        conf_edge = 0.5  # Default medium confidence
        best_edge_source = None

    # Compute weights
    total = conf_node + conf_edge + 0.01  # Avoid division by zero
    w_node_raw = conf_node / total

    # Clip to [weight_clip_min, weight_clip_max]
    w_node = max(config.weight_clip_min, min(config.weight_clip_max, w_node_raw))
    w_edge = 1 - w_node

    # Best gap
    all_gaps = [s.gap for s in collection_stats.values()]
    best_gap = max(all_gaps) if all_gaps else 0.0

    context = AdaptiveScoringContext(
        collection_stats=collection_stats,
        conf_node=conf_node,
        conf_edge=conf_edge,
        w_node=w_node,
        w_edge=w_edge,
        best_gap=best_gap,
        best_node_source=best_node_source,
        best_edge_source=best_edge_source,
    )

    if debug:
        logger.debug(f"[AdaptiveContext] {context.debug_str()}")
        if best_node_source:
            logger.debug(f"[AdaptiveContext] Best node: {best_node_source}")
        if best_edge_source:
            logger.debug(f"[AdaptiveContext] Best edge: {best_edge_source}")

    return context


# ============================================================
# Final scoring: compute_lambda, compute_struct_score, compute_final_score
# ============================================================


def compute_lambda(
    conf_node: float,
    conf_edge: float,
    exact_match_bonus: float,
    best_gap: float,
    semantic: float,
    config: Any,
) -> float:
    """
    Compute the fusion coefficient lambda between semantic and structural signals.

    Higher lambda trusts semantic more; lower lambda trusts structural more.

    Args:
        conf_node: Node confidence.
        conf_edge: Edge confidence.
        exact_match_bonus: Exact match bonus (used to determine boost trigger).
        best_gap: Maximum gap across all collections.
        semantic: Semantic score.
        config: EpisodicConfig object.

    Returns:
        float: Fusion coefficient in [lambda_min, lambda_max].
    """
    # Base value: take highest confidence
    lambda_base = max(conf_node, conf_edge)

    # Exact match boost
    if exact_match_bonus > config.exact_match_threshold_strong:  # 0.1
        lambda_match = config.lambda_match_strong  # 0.2
    elif exact_match_bonus > config.exact_match_threshold_weak:  # 0.05
        lambda_match = config.lambda_match_weak  # 0.1
    else:
        lambda_match = 0.0

    # Gap boost
    if best_gap > config.gap_high:  # 0.15
        lambda_gap = config.lambda_gap_high  # 0.15
    elif best_gap > (config.gap_high + config.gap_low) / 2:  # 0.1
        lambda_gap = config.lambda_gap_mid  # 0.1
    else:
        lambda_gap = 0.0

    # Extra boost when semantic score is very good
    if semantic < config.semantic_threshold_excellent and exact_match_bonus > config.exact_match_threshold_strong:
        # semantic < 0.1 with strong exact match
        lambda_semantic = config.lambda_semantic_boost  # 0.3
    elif semantic < config.semantic_threshold_good:  # 0.2
        lambda_semantic = config.lambda_semantic_mid  # 0.15
    else:
        lambda_semantic = 0.0

    # Combine
    total = lambda_base + lambda_match + lambda_gap + lambda_semantic

    # Clip to [lambda_min, lambda_max]
    return max(config.lambda_min, min(config.lambda_max, total))


def compute_struct_score(ep_rank: int, config: Any) -> float:
    """
    Compute structural score (decay function).

    Uses 1 - 1/(1 + rank x decay) ensuring:
    - rank=0 -> struct=0
    - rank increases -> struct asymptotes to 1
    - Range fixed in [0, 1)

    Args:
        ep_rank: Episode rank (0-based).
        config: EpisodicConfig object.

    Returns:
        float: Structural score in [0, 1).
    """
    return 1 - 1 / (1 + ep_rank * config.struct_decay_factor)


def compute_semantic_score(
    node_score: float,
    edge_score: float,
    w_node: float,
    w_edge: float,
    consistency_bonus: float = 0.0,
) -> float:
    """
    Compute semantic score.

    Args:
        node_score: Normalized node score [0, 1].
        edge_score: Normalized edge score [0, 1].
        w_node: Node weight.
        w_edge: Edge weight.
        consistency_bonus: Consistency bonus (optional).

    Returns:
        float: Semantic score, lower is better.
    """
    semantic = w_node * node_score + w_edge * edge_score
    semantic = semantic - consistency_bonus
    return max(0.0, semantic)


def compute_final_score(semantic: float, ep_rank: int, lambda_value: float, config: Any) -> float:
    """
    Compute final ranking score.

    final = lambda x semantic + (1-lambda) x struct

    Args:
        semantic: Semantic score.
        ep_rank: Episode rank.
        lambda_value: Fusion coefficient.
        config: EpisodicConfig object.

    Returns:
        float: Final score, lower is better.
    """
    struct = compute_struct_score(ep_rank, config)
    return lambda_value * semantic + (1 - lambda_value) * struct


# ============================================================
# Helper functions
# ============================================================


def get_exact_match_bonus(
    node_score: float,
    edge_score: float,
    threshold_strong: float = 0.05,
    threshold_weak: float = 0.10,
) -> float:
    """
    Estimate exact match bonus (proxy metric).

    Uses vector scores as a proxy to determine if there is an exact match.
    Very low scores typically indicate exact text matches.

    Args:
        node_score: Node vector score.
        edge_score: Edge vector score.
        threshold_strong: Strong match threshold.
        threshold_weak: Weak match threshold.

    Returns:
        float: Estimated exact match bonus.
    """
    min_score = min(node_score, edge_score)

    if min_score < threshold_strong:
        return 0.15  # Strong exact match
    elif min_score < threshold_weak:
        return 0.08  # Moderate exact match
    else:
        return 0.0


def is_node_collection(collection_name: str) -> bool:
    """
    Determine if a collection is a node type.

    Args:
        collection_name: Collection name.

    Returns:
        bool: True if this is a node collection.

    Note: Must exclude edge collections first, since 'name' would match 'RelationType_relationship_name'.
    """
    # Check edge collection first
    is_edge = "relationship" in collection_name.lower() or "edge" in collection_name.lower()
    if is_edge:
        return False

    return (
        "search_text" in collection_name
        or "anchor_text" in collection_name
        or "name" in collection_name
        or "summary" in collection_name
    )
