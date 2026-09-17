# m_flow/memory/episodic/episodic_ingestion_config.py
"""
Episodic Memory ingestion configuration module.

Centralized management of all ingestion-related configuration parameters, supporting:
1. Environment variable override
2. Code default values
3. Runtime dynamic configuration

Usage:
    from m_flow.memory.episodic import get_ingestion_config, EpisodicIngestionConfig

    # Use default config
    config = get_ingestion_config()

    # Custom config
    config = EpisodicIngestionConfig(
        enable_semantic_merge=True,
        max_new_facets_per_batch=30,
    )
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

# Import utility functions from unified module
from m_flow.memory.episodic.env_utils import (
    as_bool_env as _as_bool_env,
    as_float_env as _as_float_env,
    as_int_env as _as_int_env,
)


@dataclass
class EpisodicIngestionConfig:
    """
    Episodic Memory ingestion configuration.

    Configuration priority:
    1. Function parameters (highest)
    2. Environment variables
    3. Dataclass default values (lowest)

    Attributes:
        # ============================================================
        # Feature flags
        # ============================================================
        enable_semantic_merge: Whether to enable semantic merge (merge similar Facets)
        enable_episode_routing: Whether to enable cross-batch incremental update routing
        enable_facet_points: Whether to enable FacetPoint three-layer structure
        enable_llm_entity_for_routing: Whether to use LLM to extract entity names for routing
        enable_point_refiner: Whether to enable FacetPoint quality optimization
        mock_episodic: Whether to use mock mode (for testing)

        # ============================================================
        # Numerical thresholds
        # ============================================================
        semantic_merge_threshold: Semantic merge similarity threshold (0.0-1.0)
        llm_concurrency_limit: LLM concurrent call limit

        # ============================================================
        # Capacity limits
        # ============================================================
        max_entities_per_episode: Maximum entities per Episode (0=unlimited)
        max_new_facets_per_batch: Maximum new Facets per batch
        max_existing_facets_in_prompt: Maximum existing Facets in prompt
        max_chunk_summaries_in_prompt: Maximum chunk summaries in prompt
        max_candidate_entities_in_prompt: Maximum candidate entities in prompt
        max_aliases_per_facet: Maximum aliases per Facet
        aliases_text_max_chars: Maximum characters for alias text
        evidence_chunks_per_facet: Evidence chunks per Facet
        max_point_aliases_text_chars: Maximum characters for FacetPoint alias text

        # ============================================================
        # File/template configuration
        # ============================================================
        episodic_nodeset_name: MemorySpace name
        facet_points_prompt_file: FacetPoint extraction prompt file name
    """

    # ============================================================
    # Feature flags
    # ============================================================
    enable_semantic_merge: bool = False
    enable_episode_routing: bool = True
    enable_facet_points: bool = True
    enable_llm_entity_for_routing: bool = True
    enable_point_refiner: bool = True
    mock_episodic: bool = False

    # ============================================================
    # Numerical thresholds
    # ============================================================
    semantic_merge_threshold: float = 0.90
    llm_concurrency_limit: int = 15

    # ============================================================
    # Capacity limits
    # ============================================================
    max_entities_per_episode: int = 0  # 0 = unlimited
    max_new_facets_per_batch: int = 20
    max_existing_facets_in_prompt: int = 60
    max_chunk_summaries_in_prompt: int = 40
    max_candidate_entities_in_prompt: int = 25
    max_aliases_per_facet: int = 10
    aliases_text_max_chars: int = 400
    evidence_chunks_per_facet: int = 3
    max_point_aliases_text_chars: int = 400

    # ============================================================
    # File/template configuration
    # ============================================================
    episodic_nodeset_name: str = "Episodic"
    facet_points_prompt_file: str = "episodic_extract_facet_points.txt"

    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.semantic_merge_threshold <= 1.0:
            raise ValueError(
                f"semantic_merge_threshold must be between 0.0 and 1.0, got {self.semantic_merge_threshold}"
            )
        if self.llm_concurrency_limit < 1:
            raise ValueError(f"llm_concurrency_limit must be >= 1, got {self.llm_concurrency_limit}")
        if self.max_new_facets_per_batch < 1:
            raise ValueError(f"max_new_facets_per_batch must be >= 1, got {self.max_new_facets_per_batch}")


def get_ingestion_config() -> EpisodicIngestionConfig:
    """
    Get ingestion configuration instance.

    Read configuration from environment variables, use defaults for unset values.

    Environment variable mapping:
        MFLOW_EPISODIC_ENABLE_SEMANTIC_MERGE → enable_semantic_merge
        MFLOW_EPISODIC_SEMANTIC_MERGE_THRESHOLD → semantic_merge_threshold
        MFLOW_EPISODIC_ENABLE_ROUTING → enable_episode_routing
        MFLOW_EPISODIC_ENABLE_FACET_POINTS → enable_facet_points
        MFLOW_EPISODIC_USE_LLM_ENTITY_FOR_ROUTING → enable_llm_entity_for_routing
        MFLOW_EPISODIC_POINT_REFINER → enable_point_refiner
        MFLOW_LLM_CONCURRENCY_LIMIT → llm_concurrency_limit
        MOCK_EPISODIC → mock_episodic
        MFLOW_EPISODIC_FACET_POINTS_PROMPT → facet_points_prompt_file

    Returns:
        EpisodicIngestionConfig instance
    """
    return EpisodicIngestionConfig(
        # Feature flags
        enable_semantic_merge=_as_bool_env("MFLOW_EPISODIC_ENABLE_SEMANTIC_MERGE", False),
        enable_episode_routing=_as_bool_env("MFLOW_EPISODIC_ENABLE_ROUTING", True),
        enable_facet_points=_as_bool_env("MFLOW_EPISODIC_ENABLE_FACET_POINTS", True),
        enable_llm_entity_for_routing=_as_bool_env("MFLOW_EPISODIC_USE_LLM_ENTITY_FOR_ROUTING", True),
        enable_point_refiner=_as_bool_env("MFLOW_EPISODIC_POINT_REFINER", True),
        mock_episodic=_as_bool_env("MOCK_EPISODIC", False),
        # Numerical thresholds
        semantic_merge_threshold=_as_float_env("MFLOW_EPISODIC_SEMANTIC_MERGE_THRESHOLD", 0.90),
        llm_concurrency_limit=_as_int_env("MFLOW_LLM_CONCURRENCY_LIMIT", 20),
        # File configuration
        facet_points_prompt_file=os.getenv("MFLOW_EPISODIC_FACET_POINTS_PROMPT", "episodic_extract_facet_points.txt"),
    )


def merge_config_with_params(
    config: Optional[EpisodicIngestionConfig],
    *,
    enable_semantic_merge: Optional[bool] = None,
    semantic_merge_threshold: Optional[float] = None,
    enable_episode_routing: Optional[bool] = None,
    enable_facet_points: Optional[bool] = None,
    enable_llm_entity_for_routing: Optional[bool] = None,
    episodic_nodeset_name: Optional[str] = None,
    max_entities_per_episode: Optional[int] = None,
    max_new_facets_per_batch: Optional[int] = None,
    max_existing_facets_in_prompt: Optional[int] = None,
    max_chunk_summaries_in_prompt: Optional[int] = None,
    max_candidate_entities_in_prompt: Optional[int] = None,
    max_aliases_per_facet: Optional[int] = None,
    aliases_text_max_chars: Optional[int] = None,
    evidence_chunks_per_facet: Optional[int] = None,
    facet_points_prompt_file: Optional[str] = None,
    max_point_aliases_text_chars: Optional[int] = None,
) -> EpisodicIngestionConfig:
    """
    Merge configuration object and function parameters.

    Priority: function parameters > configuration object > default values

    This function is used to maintain backward compatibility of write_episodic_memories():
    - If caller passes parameters, use passed values
    - If caller doesn't pass parameters (None), use configuration object values
    - If no configuration object, read from environment variables

    Args:
        config: Optional configuration object
        **kwargs: Optional override parameters

    Returns:
        Merged configuration object
    """
    # If no configuration object provided, read from environment variables
    if config is None:
        config = get_ingestion_config()

    # Function parameters override configuration object
    return EpisodicIngestionConfig(
        # Feature flags
        enable_semantic_merge=(
            enable_semantic_merge if enable_semantic_merge is not None else config.enable_semantic_merge
        ),
        enable_episode_routing=(
            enable_episode_routing if enable_episode_routing is not None else config.enable_episode_routing
        ),
        enable_facet_points=(enable_facet_points if enable_facet_points is not None else config.enable_facet_points),
        enable_llm_entity_for_routing=(
            enable_llm_entity_for_routing
            if enable_llm_entity_for_routing is not None
            else config.enable_llm_entity_for_routing
        ),
        enable_point_refiner=config.enable_point_refiner,
        mock_episodic=config.mock_episodic,
        # Numerical thresholds
        semantic_merge_threshold=(
            semantic_merge_threshold if semantic_merge_threshold is not None else config.semantic_merge_threshold
        ),
        llm_concurrency_limit=config.llm_concurrency_limit,
        # Capacity limits
        max_entities_per_episode=(
            max_entities_per_episode if max_entities_per_episode is not None else config.max_entities_per_episode
        ),
        max_new_facets_per_batch=(
            max_new_facets_per_batch if max_new_facets_per_batch is not None else config.max_new_facets_per_batch
        ),
        max_existing_facets_in_prompt=(
            max_existing_facets_in_prompt
            if max_existing_facets_in_prompt is not None
            else config.max_existing_facets_in_prompt
        ),
        max_chunk_summaries_in_prompt=(
            max_chunk_summaries_in_prompt
            if max_chunk_summaries_in_prompt is not None
            else config.max_chunk_summaries_in_prompt
        ),
        max_candidate_entities_in_prompt=(
            max_candidate_entities_in_prompt
            if max_candidate_entities_in_prompt is not None
            else config.max_candidate_entities_in_prompt
        ),
        max_aliases_per_facet=(
            max_aliases_per_facet if max_aliases_per_facet is not None else config.max_aliases_per_facet
        ),
        aliases_text_max_chars=(
            aliases_text_max_chars if aliases_text_max_chars is not None else config.aliases_text_max_chars
        ),
        evidence_chunks_per_facet=(
            evidence_chunks_per_facet if evidence_chunks_per_facet is not None else config.evidence_chunks_per_facet
        ),
        max_point_aliases_text_chars=(
            max_point_aliases_text_chars
            if max_point_aliases_text_chars is not None
            else config.max_point_aliases_text_chars
        ),
        # File configuration
        episodic_nodeset_name=(
            episodic_nodeset_name if episodic_nodeset_name is not None else config.episodic_nodeset_name
        ),
        facet_points_prompt_file=(
            facet_points_prompt_file if facet_points_prompt_file is not None else config.facet_points_prompt_file
        ),
    )
