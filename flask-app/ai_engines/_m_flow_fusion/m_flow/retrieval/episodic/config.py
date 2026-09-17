"""
Episodic retrieval configuration management.

Centralizes all environment variables and default configurations to avoid scattered settings.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class EpisodicConfig:
    """Unified configuration for Episodic retrieval."""

    # Retrieval parameters
    top_k: int = 10  # Default return 10 Episodes
    wide_search_top_k: int = 100
    max_relevant_ids: int = 300  # Restored original value
    triplet_distance_penalty: float = 3.5

    # Path cost parameters
    edge_miss_cost: float = 0.9
    hop_cost: float = 0.05
    direct_episode_penalty: float = 0.3

    # Output control
    max_facets_per_episode: int = 4
    max_points_per_facet: int = 8

    # Display mode:
    #   "summary" - Show only Episode summary (default, concise for LLM)
    #   "detail"  - Show Facet + Entity edges (no Episode summary, no FacetPoint)
    display_mode: str = "summary"

    # Vector collections
    # Excludes Facet_aliases_text and FacetPoint_aliases_text (low coverage, prone to false matches)
    collections: List[str] = field(
        default_factory=lambda: [
            "Episode_summary",
            "Facet_search_text",
            "Facet_anchor_text",
            "FacetPoint_search_text",
            "Entity_name",
            "Concept_name",  # Backward compat: old data may use this collection
            "RelationType_relationship_name",
        ]
    )

    # Node property projection
    properties_to_project: List[str] = field(
        default_factory=lambda: [
            "id",
            "name",
            "type",
            "summary",
            "signature",  # Episode
            "facet_type",
            "search_text",
            "anchor_text",
            "description",  # Facet
            "text",  # Generic
            # Time fields for graph projection
            "created_at",
            "updated_at",
            "mentioned_time_start_ms",
            "mentioned_time_end_ms",
            "mentioned_time_confidence",
            "mentioned_time_text",  # Human-readable time text for LLM context
        ]
    )

    # MemorySpace name
    episodic_nodeset_name: str = "Episodic"
    strict_nodeset_filtering: bool = True

    # Feature flags
    enable_hybrid_search: bool = True
    hybrid_threshold: int = 3  # Enable hybrid search when core words <= this value

    # Exact match bonus
    full_number_match_bonus: float = 0.12
    partial_number_match_bonus: float = 0.03
    english_match_bonus: float = 0.08
    keyword_match_bonus: float = 0.15

    # ====== Adaptive scoring configuration ======

    # Feature flag
    enable_adaptive_weights: bool = True

    # Collection distance baselines - used for confidence calculation
    # Baseline represents the "average" raw distance for this collection, ratio = raw_distance / baseline
    # Below baseline means good match quality, above baseline means poor match quality
    collection_baselines: Dict[str, float] = field(
        default_factory=lambda: {
            "FacetPoint_search_text": 0.50,  # Short text, precise embedding
            "Facet_search_text": 0.60,  # Medium-length text
            "Facet_anchor_text": 0.60,  # Anchor text
            "RelationType_relationship_name": 0.56,  # Edge description text
            "Entity_name": 0.68,  # Entity name (current)
            "Concept_name": 0.68,  # Legacy alias, same baseline
            "Episode_summary": 1.06,  # Long text summary
        }
    )
    default_baseline: float = 0.70  # Default baseline for unknown collections

    # f_dist thresholds - distance factor calculation
    # ratio < ratio_good -> f_dist = 1.0 (very good)
    # ratio_good <= ratio < ratio_avg -> linear decay to 0.5
    # ratio_avg <= ratio < ratio_poor -> linear decay to 0.3
    # ratio >= ratio_poor -> approaches 0.1
    ratio_good: float = 0.5  # Below this value -> very good
    ratio_avg: float = 1.0  # Baseline level
    ratio_poor: float = 1.5  # Above this value -> very poor

    # f_gap thresholds - Gap factor calculation
    # gap > gap_high -> f_gap = 1.0 (very significant)
    # gap_low < gap <= gap_high -> linear interpolation 0.6 -> 1.0
    # gap_trivial < gap <= gap_low -> linear interpolation 0.2 -> 0.6
    # gap <= gap_trivial -> f_gap = 0.2 (indistinguishable)
    gap_trivial: float = 0.01  # Below this value -> indistinguishable
    gap_low: float = 0.05  # Moderate distinction
    gap_high: float = 0.15  # Above this value -> very significant

    # Weight clipping range - prevent completely ignoring a signal type
    weight_clip_min: float = 0.2  # Minimum value for W_node/W_edge
    weight_clip_max: float = 0.8  # Maximum value for W_node/W_edge

    # Lambda range - fusion coefficient between semantic and structural signals
    # Higher lambda trusts semantic more, lower lambda trusts structural more
    lambda_min: float = 0.3
    lambda_max: float = 0.95

    # Lambda boost coefficients - additional lambda boosts triggered by various conditions
    lambda_match_strong: float = 0.2  # When exact_match_bonus > 0.1
    lambda_match_weak: float = 0.1  # When exact_match_bonus > 0.05
    lambda_gap_high: float = 0.15  # When best_gap > 0.15
    lambda_gap_mid: float = 0.10  # When best_gap > 0.1
    lambda_semantic_boost: float = 0.3  # When semantic < 0.1 with exact match
    lambda_semantic_mid: float = 0.15  # When semantic < 0.2

    # Exact match thresholds - used to determine if lambda boost is triggered
    exact_match_threshold_strong: float = 0.10
    exact_match_threshold_weak: float = 0.05
    semantic_threshold_excellent: float = 0.10
    semantic_threshold_good: float = 0.20

    # Structural score decay - struct = 1 - 1/(1 + ep_rank x decay)
    struct_decay_factor: float = 0.5

    # Consistency bonus (optional feature)
    enable_consistency_bonus: bool = False
    consistency_bonus_per_hit: float = 0.08

    # Debug configuration
    adaptive_debug_mode: bool = False

    # ====== Time enhancement configuration ======

    # Feature flag
    enable_time_bonus: bool = True

    # Time bonus strength
    time_bonus_max: float = 0.06  # Maximum time bonus
    time_score_floor: float = 0.08  # Score floor (avoid excessive suppression)
    time_bonus_bundle: float = 0.04  # Bundle-level time bonus

    # Confidence threshold
    time_conf_min: float = 0.4  # No bonus if query time confidence below this value

    # Match weights
    time_mentioned_weight: float = 1.0  # Weight for mentioned_time
    time_created_at_weight: float = 0.5  # Weight for created_at (typically lower)

    # Recall expansion (when query contains time)
    time_wide_multiplier: float = 2.0  # Multiplier to expand candidate pool
    time_wide_cap: int = 300  # Candidate pool cap

    # Debug
    time_debug_mode: bool = False

    # ====== Mismatch Penalty configuration ======
    # Penalty when query explicitly contains time but candidate time doesn't match
    enable_mismatch_penalty: bool = False  # Whether to enable mismatch penalty
    mismatch_penalty_max: float = 0.03  # Maximum penalty value
    mismatch_conf_threshold: float = 0.7  # Query time confidence threshold
    mismatch_require_candidate_time: bool = True  # Whether to require candidate to have time field

    def get_baseline(self, collection_name: str) -> float:
        """Get baseline value for the specified collection."""
        return self.collection_baselines.get(collection_name, self.default_baseline)


def get_episodic_config() -> EpisodicConfig:
    """
    Load configuration from environment variables, use defaults if not set.

    Environment variables:
        MFLOW_EPISODIC_TOP_K
        MFLOW_EPISODIC_WIDE_SEARCH_TOP_K
        MFLOW_EPISODIC_EDGE_MISS_COST
        MFLOW_EPISODIC_HOP_COST
        MFLOW_EPISODIC_MAX_FACETS_PER_EPISODE
        MFLOW_EPISODIC_MAX_POINTS_PER_FACET

        # Adaptive scoring related environment variables
        EPISODIC_ENABLE_ADAPTIVE
        EPISODIC_ADAPTIVE_DEBUG
        EPISODIC_DEFAULT_BASELINE
        EPISODIC_LAMBDA_MIN
        EPISODIC_LAMBDA_MAX
    """
    config = EpisodicConfig()

    # Override from environment variables - basic configuration
    if val := os.getenv("MFLOW_EPISODIC_TOP_K"):
        config.top_k = int(val)
    if val := os.getenv("MFLOW_EPISODIC_WIDE_SEARCH_TOP_K"):
        config.wide_search_top_k = int(val)
    if val := os.getenv("MFLOW_EPISODIC_EDGE_MISS_COST"):
        config.edge_miss_cost = float(val)
    if val := os.getenv("MFLOW_EPISODIC_HOP_COST"):
        config.hop_cost = float(val)
    if val := os.getenv("MFLOW_EPISODIC_MAX_FACETS_PER_EPISODE"):
        config.max_facets_per_episode = int(val)
    if val := os.getenv("MFLOW_EPISODIC_MAX_POINTS_PER_FACET"):
        config.max_points_per_facet = int(val)
    if val := os.getenv("MFLOW_EPISODIC_DISPLAY_MODE"):
        if val.lower() in ("detail", "summary"):
            config.display_mode = val.lower()

    # Override from environment variables - adaptive scoring configuration
    if val := os.getenv("EPISODIC_ENABLE_ADAPTIVE"):
        config.enable_adaptive_weights = val.lower() in ("1", "true", "yes")
    if val := os.getenv("EPISODIC_ADAPTIVE_DEBUG"):
        config.adaptive_debug_mode = val.lower() in ("1", "true", "yes")
    if val := os.getenv("EPISODIC_DEFAULT_BASELINE"):
        config.default_baseline = float(val)
    if val := os.getenv("EPISODIC_LAMBDA_MIN"):
        config.lambda_min = float(val)
    if val := os.getenv("EPISODIC_LAMBDA_MAX"):
        config.lambda_max = float(val)
    if val := os.getenv("EPISODIC_WEIGHT_CLIP_MIN"):
        config.weight_clip_min = float(val)
    if val := os.getenv("EPISODIC_WEIGHT_CLIP_MAX"):
        config.weight_clip_max = float(val)

    # Override from environment variables - time enhancement configuration
    if val := os.getenv("EPISODIC_ENABLE_TIME_BONUS"):
        config.enable_time_bonus = val.lower() in ("1", "true", "yes")
    if val := os.getenv("EPISODIC_TIME_BONUS_MAX"):
        config.time_bonus_max = float(val)
    if val := os.getenv("EPISODIC_TIME_SCORE_FLOOR"):
        config.time_score_floor = float(val)
    if val := os.getenv("EPISODIC_TIME_CONF_MIN"):
        config.time_conf_min = float(val)
    if val := os.getenv("EPISODIC_TIME_WIDE_MULTIPLIER"):
        config.time_wide_multiplier = float(val)
    if val := os.getenv("EPISODIC_TIME_WIDE_CAP"):
        config.time_wide_cap = int(val)
    if val := os.getenv("EPISODIC_TIME_DEBUG"):
        config.time_debug_mode = val.lower() in ("1", "true", "yes")

    # Mismatch penalty configuration
    if val := os.getenv("EPISODIC_ENABLE_MISMATCH_PENALTY"):
        config.enable_mismatch_penalty = val.lower() in ("1", "true", "yes")
    if val := os.getenv("EPISODIC_MISMATCH_PENALTY_MAX"):
        config.mismatch_penalty_max = float(val)
    if val := os.getenv("EPISODIC_MISMATCH_CONF_THRESHOLD"):
        config.mismatch_conf_threshold = float(val)
    if val := os.getenv("EPISODIC_MISMATCH_REQUIRE_CANDIDATE_TIME"):
        config.mismatch_require_candidate_time = val.lower() in ("1", "true", "yes")

    return config
