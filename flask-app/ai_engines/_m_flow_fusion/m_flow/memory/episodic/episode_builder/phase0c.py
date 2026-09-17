# m_flow/memory/episodic/episode_builder/phase0c.py
"""
Phase 0C: Entity Creation and Batch Lookup

This module implements entity creation for the episode processing pipeline:
1. Generate entity IDs and canonical names for each entity
2. Batch lookup same-name existing entities (N queries → 1 query optimization)
3. Create Entity objects with entity_map and top_entities
4. Collect same_entity_edges_pending for later edge creation

Phase 4-New-C: Extracted from write_episodic_memories.py

Design:
- All closures are converted to explicit parameters
- Returns Phase0CResult with all outputs
- same_entity_edges_pending is collected and returned (not stored in closure)
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from m_flow.shared.logging_utils import get_logger

# Node ID generation
from m_flow.core.domain.utils.generate_node_id import generate_node_id

# Normalization
from m_flow.memory.episodic.normalization import normalize_for_id

# Entity lookup (extracted in Phase 2)
from m_flow.memory.episodic.utils.entity_lookup import (
    batch_find_existing_entities_by_canonical_names,
)

# Domain models
from m_flow.core.domain.models import Entity  # Entity is new name, Entity is alias

# Pipeline contexts
from m_flow.memory.episodic.episode_builder.pipeline_contexts import (
    Phase0CResult,
)

if TYPE_CHECKING:
    pass


logger = get_logger(__name__)


# ============================================================
# Main Execution Function
# ============================================================


async def execute_phase0c(
    top_entity_names: List[str],
    episode_id_str: str,
    episode_memory_types: Dict[str, str],
) -> Tuple[Phase0CResult, List[Tuple[Entity, List[Dict[str, Any]]]]]:
    """
    Execute Phase 0C: Entity creation and batch lookup.

    This phase creates Entity objects for all extracted entity names
    and performs a batch lookup for same-name entities across all episodes.

    Args:
        top_entity_names: List of entity names from Phase 0A
        episode_id_str: Episode identifier for generating entity IDs
        episode_memory_types: Mapping of episode_id to memory_type

    Returns:
        Tuple of:
        - Phase0CResult containing:
          - top_entities: List of created Entity objects
          - entity_map: Mapping from entity name to Entity object
          - existing_entities_batch: Batch lookup results for same-name entities
        - same_entity_edges_pending: List of (new_entity, existing_list) pairs
          for later edge creation

    Note:
        top_entities and entity_map share the same Entity object references.
        Modifications to objects in top_entities are visible through entity_map.
    """
    _entity_creation_start = time.time()

    # Pre-compute all Entity IDs and canonical_names (using "Entity:" prefix for backward compat)
    entity_id_map: Dict[str, str] = {}  # name -> entity_id
    canonical_map: Dict[str, str] = {}  # name -> canonical_name

    for name in top_entity_names:
        entity_id = str(generate_node_id(f"Entity:{episode_id_str}:{normalize_for_id(name)}"))
        canonical = normalize_for_id(name)
        entity_id_map[name] = entity_id
        canonical_map[name] = canonical

    # Batch find all same-name Entities (1 query instead of N)
    all_canonical_names = list(set(canonical_map.values()))
    all_entity_ids = list(entity_id_map.values())

    existing_entities_batch = await batch_find_existing_entities_by_canonical_names(
        canonical_names=all_canonical_names,
        exclude_ids=all_entity_ids,
    )

    # Create Entity objects and link to existing same-name entities
    entity_map: Dict[str, Entity] = {}
    top_entities: List[Entity] = []
    same_entity_edges_pending: List[Tuple[Entity, List[Dict[str, Any]]]] = []

    # Determine memory_type for entities in this Episode
    # Use the Episode's memory_type so entities inherit the same type
    current_episode_memory_type = episode_memory_types.get(episode_id_str, "episodic")

    for name in top_entity_names:
        entity_id = entity_id_map[name]
        canonical = canonical_map[name]

        entity = Entity(
            id=entity_id,
            name=name,
            description="",  # Will be filled by Entity Description LLM
            canonical_name=canonical,
            memory_type=current_episode_memory_type,  # Inherit from Episode's memory_type
        )
        entity_map[name] = entity
        top_entities.append(entity)

        # Get same-name entities from batch lookup result
        existing_entities = existing_entities_batch.get(canonical, [])
        if existing_entities:
            same_entity_edges_pending.append((entity, existing_entities))
            logger.debug(
                f"[episodic] Entity '{name}' found {len(existing_entities)} same-name "
                f"entities across episodes for linking"
            )

    _entity_creation_elapsed = time.time() - _entity_creation_start
    logger.info(
        f"[episodic] Phase 0C Entity creation + batch lookup: {_entity_creation_elapsed:.2f}s "
        f"({len(top_entities)} entities, {sum(len(v) for v in existing_entities_batch.values())} existing)"
    )

    result = Phase0CResult(
        top_entities=top_entities,
        entity_map=entity_map,
        existing_entities_batch=existing_entities_batch,
    )

    return result, same_entity_edges_pending


# ============================================================
# Module exports
# ============================================================

__all__ = [
    "execute_phase0c",
]
