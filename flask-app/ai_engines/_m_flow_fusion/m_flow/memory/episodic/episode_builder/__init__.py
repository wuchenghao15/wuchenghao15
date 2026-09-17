# m_flow/memory/episodic/episode_builder/__init__.py
"""
Episode Builder Module - Pipeline Infrastructure for Episodic Memory Processing

This module provides the pipeline infrastructure for processing episodes in a modular,
maintainable way. It breaks down the large write_episodic_memories function into
distinct, testable stages.

Phase 4-New-A: Created as part of the large file refactoring plan.

Directory Structure:
    episode_builder/
    ├── __init__.py              # This file - module exports
    ├── pipeline_contexts.py     # Data classes for pipeline stages
    ├── phase0a.py              # Phase 0A: Three-way parallel (entity names, facets, matcher)
    ├── phase0c.py              # Phase 0C: Entity creation
    ├── step1_facet_prep.py     # Step 1: Time calculation + Facet preparation
    ├── step2_parallel.py       # Step 2: Parallel entity description + facetpoint extraction
    └── step35_node_creation.py # Step 3-5: Node and edge creation
"""

from __future__ import annotations

# Pipeline context and result data classes
from m_flow.memory.episodic.episode_builder.pipeline_contexts import (
    EpisodeConfig,
    EpisodeContext,
    EpisodeProcessingState,
    Phase0AResult,
    Phase0CResult,
    Step1Result,
    Step2Result,
)

# Phase 0A: Three-way parallel optimization
from m_flow.memory.episodic.episode_builder.phase0a import (
    execute_phase0a,
)

# Phase 0C: Entity creation and batch lookup
from m_flow.memory.episodic.episode_builder.phase0c import (
    execute_phase0c,
)

# Step 1: Time calculation + Facet preparation
from m_flow.memory.episodic.episode_builder.step1_facet_prep import (
    execute_step1,
)

# Step 2: Parallel Entity Description + FacetPoint Extraction
from m_flow.memory.episodic.episode_builder.step2_parallel import (
    execute_step2,
)

# Step 3-5: Node and Edge Creation
from m_flow.memory.episodic.episode_builder.step35_node_edge_creation import (
    _build_has_facet_edges,
    _build_involves_entity_edges,
    _queue_facet_entity_edges,
    _collect_same_entity_as_edges,
    _build_includes_chunk_edges,
    _create_episode,
)

__all__ = [
    # Configuration
    "EpisodeConfig",
    # Context
    "EpisodeContext",
    # State accumulator
    "EpisodeProcessingState",
    # Stage results
    "Phase0AResult",
    "Phase0CResult",
    "Step1Result",
    "Step2Result",
    # Phase executors
    "execute_phase0a",
    "execute_phase0c",
    "execute_step1",
    "execute_step2",
    # Step 3-5 functions
    "_build_has_facet_edges",
    "_build_involves_entity_edges",
    "_queue_facet_entity_edges",
    "_collect_same_entity_as_edges",
    "_build_includes_chunk_edges",
    "_create_episode",
]
