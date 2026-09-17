# m_flow/memory/episodic/__init__.py
"""
Episodic Memory Tasks

Stage 2: Episode + Facet + Rich semantic edge writing
Stage 5: Write quality enhancement
Stage 5.8-5.13: Aliases fallback recall + semantic synonym merging
Stage 6: Cross-batch incremental update (Episode Router)
Stage X: FacetPoint three-layer conical structure
Stage 4 (New): Migration and convergence (aliases -> FacetPoints)
"""

from .write_episodic_memories import write_episodic_memories
from .edge_writers import (
    write_same_entity_edges,
    write_facet_entity_edges,
)
from .models import (
    EpisodicFacetDraft,
    EpisodicAliasUpdate,
    EpisodicWriteDraft,
    EpisodeCandidate,
    RouteDecision,
    # Content Routing Models
    RoutingType,
    EpisodicSegment,
    ContentRoutingResult,
)
from .aliases import is_bad_alias, clean_aliases, make_aliases_text
from .semantic_merge import SemanticFacetMatcher, ExistingFacetInfo
from .episode_router import route_episode_id_for_doc
from .migrate_aliases_to_facet_points import migrate_aliases_to_facet_points
from .facet_points_refiner import (
    refine_facet_points,
    is_bad_point_handle,
    semantic_dedup_points,
    RefineStats,
)
from .llm_call_tracker import (
    get_llm_tracker,
    LLMCallTracker,
    LLMCallRecord,
    tracked_llm_call,
)
from .ingestion_logger import (
    IngestionLogger,
    IngestionMetrics,
    IngestionPhase,
    create_ingestion_logger,
)
from .episodic_ingestion_config import (
    EpisodicIngestionConfig,
    get_ingestion_config,
    merge_config_with_params,
)

# Step 3D: New module exports
from .normalization import (
    normalize_for_compare,
    normalize_for_id,
    truncate,
    is_bad_search_text,
    # Search text quality evaluation
    evaluate_search_text,
    SearchTextQuality,
    SearchTextEvaluation,
)
from .context_vars import (
    get_pending_same_entity_edges,
    add_pending_same_entity_edge,
    get_and_clear_pending_same_entity_edges,
    get_pending_facet_entity_edges,
    add_pending_facet_entity_edge,
    get_and_clear_pending_facet_entity_edges,
)
from .edge_text_generators import (
    make_has_facet_edge_text,
    make_involves_entity_edge_text,
    make_same_entity_as_edge_text,
    make_supported_by_edge_text,
    make_includes_chunk_edge_text,
    make_has_point_edge_text,
    make_facet_involves_entity_edge_text,
)

# Facet-Entity Matching
from .facet_entity_matcher import (
    match_entities_to_facets,
    build_facet_entity_edges,
)

# Episode state query
from .state import (
    EpisodeState,
    ExistingFacet,
    fetch_episode_state,
    ExistingFacetPoint,
    fetch_facet_points,
)

# LLM task functions
from .llm_tasks import (
    llm_select_entities,
    llm_extract_entity_names,
    llm_write_entity_descriptions,
    llm_extract_facet_points,
)

# Environment variable utility functions
from .env_utils import (
    as_bool_env,
    as_int_env,
    as_float_env,
)

# Content Routing (Sentence-Level Classification)
from .sentence_level_routing import (
    route_content_v2,  # Preserved for backward compatibility
    get_sentence_classifications,
    has_v2_routing,  # Preserved for backward compatibility
    get_episodic_sentences,
    get_atomic_sentences,
    group_by_event,
)
from .sentence_splitter import (
    smart_split_sentences,
    split_with_positions,
    count_sentences,
    is_single_sentence,
)
from .models import (
    SentenceClassification,
    SentenceRoutingResult,
    EventClassification,
)

# Episode Size Check
from .episode_size_check import (
    run_episode_size_check,
    detect_oversized_episodes,
    audit_episode,
    execute_split,
    adapt_threshold,
    EpisodeSizeCheckConfig,
    get_size_check_config,
    EpisodeStats,
    SplitSuggestion,
    AuditResult,
    SplitHistoryEntry,
)

__all__ = [
    # Core tasks
    "write_episodic_memories",
    "write_same_entity_edges",
    "write_facet_entity_edges",
    # LLM output models
    "EpisodicFacetDraft",
    "EpisodicAliasUpdate",
    "EpisodicWriteDraft",
    # Content Routing Models
    "RoutingType",
    "EpisodicSegment",
    "ContentRoutingResult",
    # Alias utilities
    "is_bad_alias",
    "clean_aliases",
    "make_aliases_text",
    # Semantic merging
    "SemanticFacetMatcher",
    "ExistingFacetInfo",
    # Episode Router
    "route_episode_id_for_doc",
    "EpisodeCandidate",
    "RouteDecision",
    # Migration and convergence
    "migrate_aliases_to_facet_points",
    # Quality enhancement
    "refine_facet_points",
    "is_bad_point_handle",
    "semantic_dedup_points",
    "RefineStats",
    # LLM call tracking
    "get_llm_tracker",
    "LLMCallTracker",
    "LLMCallRecord",
    "tracked_llm_call",
    # Ingestion flow logging (Step 2)
    "IngestionLogger",
    "IngestionMetrics",
    "IngestionPhase",
    "create_ingestion_logger",
    # Ingestion configuration (Step 3A)
    "EpisodicIngestionConfig",
    "get_ingestion_config",
    "merge_config_with_params",
    # Step 3D: Modular exports
    # normalization
    "normalize_for_compare",
    "normalize_for_id",
    "truncate",
    "is_bad_search_text",
    # Search text quality evaluation
    "evaluate_search_text",
    "SearchTextQuality",
    "SearchTextEvaluation",
    # context_vars
    "get_pending_same_entity_edges",
    "add_pending_same_entity_edge",
    "get_and_clear_pending_same_entity_edges",
    "get_pending_facet_entity_edges",
    "add_pending_facet_entity_edge",
    "get_and_clear_pending_facet_entity_edges",
    # edge_text_generators
    "make_has_facet_edge_text",
    "make_involves_entity_edge_text",
    "make_same_entity_as_edge_text",
    "make_supported_by_edge_text",
    "make_includes_chunk_edge_text",
    "make_has_point_edge_text",
    "make_facet_involves_entity_edge_text",
    # Facet-Entity Matching
    "match_entities_to_facets",
    "build_facet_entity_edges",
    # Episode state query
    "EpisodeState",
    "ExistingFacet",
    "fetch_episode_state",
    "ExistingFacetPoint",
    "fetch_facet_points",
    # LLM tasks
    "llm_select_entities",
    "llm_extract_entity_names",
    "llm_write_entity_descriptions",
    "llm_extract_facet_points",
    # Environment variable utilities
    "as_bool_env",
    "as_int_env",
    "as_float_env",
    # Content Routing (Sentence-Level)
    "route_content_v2",  # Preserved for backward compatibility
    "get_sentence_classifications",
    "has_v2_routing",
    "get_episodic_sentences",
    "get_atomic_sentences",
    "group_by_event",
    # Sentence Splitter
    "smart_split_sentences",
    "split_with_positions",
    "count_sentences",
    "is_single_sentence",
    # V2 Models
    "SentenceClassification",
    "SentenceRoutingResult",
    "EventClassification",
    # Episode Size Check
    "run_episode_size_check",
    "detect_oversized_episodes",
    "audit_episode",
    "execute_split",
    "adapt_threshold",
    "EpisodeSizeCheckConfig",
    "get_size_check_config",
    "EpisodeStats",
    "SplitSuggestion",
    "AuditResult",
    "SplitHistoryEntry",
]
