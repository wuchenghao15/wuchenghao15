# m_flow/memory/episodic/episode_builder/step2_parallel.py
"""
Step 2: Parallel Entity Description + FacetPoint Extraction

This module implements the parallel LLM processing phase:
1. Entity Description Task: Batch LLM calls to generate entity descriptions
2. FacetPoint Extraction Task: Per-facet LLM calls to extract FacetPoints

Phase 4-New-E: Extracted from write_episodic_memories.py

Design:
- Both tasks run in parallel using asyncio.gather
- Uses global LLM semaphore for concurrency control
- Entity descriptions are merged with existing descriptions
- EntityType objects are created and cached
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from m_flow.shared.logging_utils import get_logger
from m_flow.shared.llm_concurrency import (
    get_global_llm_semaphore,
    get_llm_concurrency_limit,
)

# Node ID generation
from m_flow.core.domain.utils.generate_node_id import generate_node_id

# Normalization
from m_flow.memory.episodic.normalization import _nfkc, normalize_for_id

# LLM tasks
from m_flow.memory.episodic.llm_tasks import (
    llm_write_entity_descriptions as _llm_write_entity_descriptions,
    llm_extract_facet_points as _llm_extract_facet_points,
)

# FacetPoint refiner
from m_flow.memory.episodic.facet_points_refiner import refine_facet_points

# State utilities
from m_flow.memory.episodic.state import fetch_facet_points

# Description merger
from m_flow.memory.episodic.entity_description_merger import (
    merge_entity_description,
    increment_merge_count,
)

# Domain models
from m_flow.core.domain.models import (
    EntityType,
)  # EntityType is new, EntityType is alias

# Pipeline contexts
from m_flow.memory.episodic.episode_builder.pipeline_contexts import (
    Step2Result,
)

if TYPE_CHECKING:
    from m_flow.core.domain.models import Entity  # Entity is the new name for Entity
    from m_flow.memory.episodic.models import FacetPointDraft
    from m_flow.memory.episodic.utils.models import FacetUpdate
    from m_flow.memory.episodic.state import EpisodeState, ExistingFacet
    from m_flow.adapters.graph.graph_db_interface import GraphProvider


logger = get_logger(__name__)


def _as_bool_env(key: str, default: bool = False) -> bool:
    """Read environment variable as boolean."""
    val = os.environ.get(key, "").lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no"):
        return False
    return default


# ============================================================
# Entity Description Task
# ============================================================


async def _entity_description_task(
    top_entities: List["Entity"],
    chunk_summaries: List[str],
) -> Dict[str, Tuple[str, str]]:
    """
    Concurrently write descriptions for all entities.

    Args:
        top_entities: List of Entity objects
        chunk_summaries: List of chunk summary texts for context

    Returns:
        Dict mapping entity_name to (description, entity_type)
    """
    _global_llm_semaphore = get_global_llm_semaphore()

    all_entity_names = [e.name for e in top_entities]
    source_text_for_entities = "\n".join(chunk_summaries)

    if not all_entity_names:
        return {}

    # Split entities into batches: ceil(total / 10) batches
    total = len(all_entity_names)
    num_batches = (total + 9) // 10
    base_size = total // num_batches
    remainder = total % num_batches

    batches: List[List[str]] = []
    start = 0
    for i in range(num_batches):
        batch_size = base_size + (1 if i < remainder else 0)
        batches.append(all_entity_names[start : start + batch_size])
        start += batch_size

    logger.info(
        f"[episodic] Entity description: {total} entities -> {len(batches)} batches: {[len(b) for b in batches]}"
    )

    async def _write_batch(batch_names: List[str], batch_idx: int):
        async with _global_llm_semaphore:
            return await _llm_write_entity_descriptions(
                entity_names=batch_names,
                source_text=source_text_for_entities,
                batch_index=batch_idx,
            )

    results = await asyncio.gather(
        *[_write_batch(batch, i) for i, batch in enumerate(batches)],
        return_exceptions=True,
    )

    entity_desc_map: Dict[str, Tuple[str, str]] = {}
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"[episodic] Entity description batch failed: {r}")
            continue
        for ed in r.descriptions or []:
            n = _nfkc(ed.name)
            desc = ed.description or ""
            entity_type = getattr(ed, "entity_type", "Thing") or "Thing"
            if n and desc and n not in entity_desc_map:
                entity_desc_map[n] = (desc, entity_type)

    logger.info(f"[episodic] Entity description complete: {len(entity_desc_map)}/{len(all_entity_names)}")
    return entity_desc_map


# ============================================================
# FacetPoint Extraction Task
# ============================================================


async def _facetpoint_extraction_task(
    updates: Dict[str, "FacetUpdate"],
    existing_by_id: Dict[str, "ExistingFacet"],
    evidence_pairs: List[Tuple[Any, str]],
    graph_engine: "GraphProvider",
    enable_facet_points: bool,
    facet_points_prompt_file: str | None,
) -> Dict[str, List["FacetPointDraft"]]:
    """
    Concurrently extract FacetPoints for all facets.

    Args:
        updates: Dict of facet_id -> FacetUpdate
        existing_by_id: Dict of facet_id -> ExistingFacet
        evidence_pairs: List of (chunk, summary_text) pairs
        graph_engine: Graph database engine for fetching existing points
        enable_facet_points: Whether to enable FacetPoint extraction
        facet_points_prompt_file: Custom prompt file for extraction

    Returns:
        Dict mapping facet_id to list of FacetPointDraft
    """
    if not enable_facet_points:
        return {}

    _global_llm_semaphore = get_global_llm_semaphore()

    facets_to_process = []
    for upd in updates.values():
        if not upd.touched and upd.id in existing_by_id:
            continue
        facet_desc = upd.description.strip() if upd.description else None
        if facet_desc:
            facets_to_process.append(upd)

    if not facets_to_process:
        return {}

    logger.info(f"[episodic] FacetPoint extraction: {len(facets_to_process)} facets to process")

    # Build candidate chunks for evidence linking
    candidate_chunks_for_refiner = []
    for ch, summary_text in evidence_pairs:
        candidate_chunks_for_refiner.append(
            {
                "id": str(ch.id),
                "text": summary_text or str(getattr(ch, "text", "")),
                "chunk_index": int(getattr(ch, "chunk_index", -1)),
            }
        )

    enable_point_refiner = _as_bool_env("MFLOW_EPISODIC_POINT_REFINER", True)

    async def _extract_points_for_facet(upd) -> Tuple[str, List["FacetPointDraft"]]:
        async with _global_llm_semaphore:
            facet_desc = upd.description.strip() if upd.description else None
            if not facet_desc:
                return upd.id, []

            existing_points_list: List[str] = []
            try:
                existing_fp = await fetch_facet_points(graph_engine, upd.id)
                existing_points_list = [p.search_text for p in existing_fp if p.search_text]
            except Exception as e:
                logger.debug(f"[episodic] fetch_facet_points failed for {upd.id}: {e}")
                existing_points_list = []

            extracted: List["FacetPointDraft"] = []
            try:
                fp_result = await _llm_extract_facet_points(
                    facet_type=upd.facet_type,
                    facet_search_text=upd.search_text,
                    facet_description=facet_desc,
                    existing_points=existing_points_list,
                    prompt_file_name=facet_points_prompt_file,
                )
                extracted = list(fp_result.points or [])
            except Exception as e:
                logger.warning(f"[episodic] FacetPoint LLM failed for '{upd.search_text}': {e}")
                extracted = []

            if enable_point_refiner and extracted:
                try:
                    refined, _, _ = await refine_facet_points(
                        raw_points=extracted,
                        facet_search_text=upd.search_text,
                        facet_description=facet_desc,
                        candidate_chunks=candidate_chunks_for_refiner if candidate_chunks_for_refiner else None,
                    )
                    extracted = refined
                except Exception as e:
                    logger.warning(f"[episodic] Stage5 refiner failed for '{upd.search_text}': {e}")

            return upd.id, extracted

    results = await asyncio.gather(
        *[_extract_points_for_facet(upd) for upd in facets_to_process],
        return_exceptions=True,
    )

    fp_cache: Dict[str, List["FacetPointDraft"]] = {}
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"[episodic] FacetPoint extraction failed: {r}")
            continue
        facet_id, points = r
        fp_cache[facet_id] = points

    logger.info(f"[episodic] FacetPoint extraction complete: {len(fp_cache)} facets processed")
    return fp_cache


# ============================================================
# Post-processing: Update Entity Descriptions and Types
# ============================================================


async def _update_entity_descriptions_and_types(
    entity_context_map: Dict[str, Tuple[str, str]],
    entity_map: Dict[str, "Entity"],
    state: "EpisodeState",
) -> Dict[str, "EntityType"]:
    """
    Update entity descriptions and create EntityType objects.

    Args:
        entity_context_map: Dict mapping entity_name to (description, entity_type)
        entity_map: Dict mapping entity_name to Entity object
        state: Episode state with existing entities

    Returns:
        Dict mapping entity_type_name to EntityType object
    """
    entity_type_cache: Dict[str, EntityType] = {}

    # Build lookup for existing entities (for description merging)
    existing_entity_descs: Dict[str, str] = {normalize_for_id(e.name): e.description or "" for e in state.entities}
    existing_entity_merge_counts: Dict[str, int] = {
        normalize_for_id(e.name): e.merge_count or 0 for e in state.entities
    }

    for entity_name, desc_info in entity_context_map.items():
        if entity_name not in entity_map:
            continue

        entity_obj = entity_map[entity_name]

        # Handle both old format (str) and new format (tuple)
        if isinstance(desc_info, tuple):
            new_description, entity_type_name = desc_info
        else:
            new_description = desc_info
            entity_type_name = "Thing"

        # Smart merge descriptions
        entity_key = normalize_for_id(entity_name)
        existing_desc = existing_entity_descs.get(entity_key, "")
        if existing_desc and new_description:
            merged_desc, was_merged = await merge_entity_description(
                existing_desc=existing_desc,
                new_desc=new_description,
                entity_name=entity_name,
            )
            entity_obj.description = merged_desc

            if was_merged:
                inherited_count = existing_entity_merge_counts.get(entity_key, 0)
                entity_obj.merge_count = increment_merge_count(inherited_count)
                logger.debug(
                    f"[episodic] Entity '{entity_name}' description merged "
                    f"(merge_count={entity_obj.merge_count}, inherited={inherited_count})"
                )
            else:
                entity_obj.merge_count = existing_entity_merge_counts.get(entity_key, 0)
        else:
            entity_obj.description = new_description

        # Create or reuse EntityType (using "EntityType:" prefix for backward compat)
        if entity_type_name:
            if entity_type_name not in entity_type_cache:
                entity_type_id = generate_node_id(f"EntityType:{entity_type_name}")
                entity_type_cache[entity_type_name] = EntityType(
                    id=entity_type_id,
                    name=entity_type_name,
                    description=f"Entity type: {entity_type_name}",
                )
            entity_obj.is_a = entity_type_cache[entity_type_name]

    return entity_type_cache


# ============================================================
# Main Execution Function
# ============================================================


async def execute_step2(
    top_entities: List["Entity"],
    entity_map: Dict[str, "Entity"],
    chunk_summaries: List[str],
    updates: Dict[str, "FacetUpdate"],
    existing_by_id: Dict[str, "ExistingFacet"],
    evidence_pairs: List[Tuple[Any, str]],
    state: "EpisodeState",
    graph_engine: "GraphProvider",
    enable_facet_points: bool,
    facet_points_prompt_file: str | None,
) -> Step2Result:
    """
    Execute Step 2: Parallel Entity Description + FacetPoint Extraction.

    This step runs two LLM-heavy tasks in parallel:
    1. Entity description generation (batched)
    2. FacetPoint extraction (per-facet)

    After parallel execution, it updates entity descriptions (with merging)
    and creates EntityType objects.

    Args:
        top_entities: List of Entity objects (will be modified in-place)
        entity_map: Dict mapping entity_name to Entity (shares refs with top_entities)
        chunk_summaries: List of chunk summary texts
        updates: Dict of facet_id -> FacetUpdate (from Step 1)
        existing_by_id: Dict of facet_id -> ExistingFacet (from Step 1)
        evidence_pairs: List of (chunk, summary_text) pairs (from Step 1)
        state: Episode state from database
        graph_engine: Graph database engine
        enable_facet_points: Whether to enable FacetPoint extraction
        facet_points_prompt_file: Custom prompt file for extraction

    Returns:
        Step2Result containing:
        - entity_context_map: Dict[str, Tuple[str, str]] (name -> (desc, type))
        - facet_points_cache: Dict[str, List[FacetPointDraft]]
        - entity_type_cache: Dict[str, EntityType]

    Note:
        top_entities and entity_map are modified in-place with descriptions
        and is_a relationships.
    """
    _llm_concurrency_limit = get_llm_concurrency_limit()
    logger.info(f"[episodic] Starting parallel Entity + FacetPoint processing (concurrency={_llm_concurrency_limit})")

    _parallel_start = time.time()

    # Default values
    entity_context_map: Dict[str, Tuple[str, str]] = {}
    facet_points_cache: Dict[str, List["FacetPointDraft"]] = {}

    try:
        parallel_results = await asyncio.gather(
            _entity_description_task(
                top_entities=top_entities,
                chunk_summaries=chunk_summaries,
            ),
            _facetpoint_extraction_task(
                updates=updates,
                existing_by_id=existing_by_id,
                evidence_pairs=evidence_pairs,
                graph_engine=graph_engine,
                enable_facet_points=enable_facet_points,
                facet_points_prompt_file=facet_points_prompt_file,
            ),
            return_exceptions=True,
        )

        # Handle Entity Description result
        if isinstance(parallel_results[0], Exception):
            logger.error(f"[episodic] Entity description task failed: {parallel_results[0]}")
        else:
            entity_context_map = parallel_results[0]

        # Handle FacetPoint result
        if isinstance(parallel_results[1], Exception):
            logger.error(f"[episodic] FacetPoint extraction task failed: {parallel_results[1]}")
        else:
            facet_points_cache = parallel_results[1]

    except Exception as e:
        logger.error(f"[episodic] Parallel Entity+FacetPoint unexpected error: {e}")

    _parallel_elapsed = time.time() - _parallel_start
    logger.info(f"[episodic] Parallel Entity+FacetPoint completed in {_parallel_elapsed:.2f}s")

    # Update entity descriptions and create EntityType objects
    entity_type_cache = await _update_entity_descriptions_and_types(
        entity_context_map=entity_context_map,
        entity_map=entity_map,
        state=state,
    )

    return Step2Result(
        entity_context_map=entity_context_map,
        facet_points_cache=facet_points_cache,
        entity_type_cache=entity_type_cache,
    )


# ============================================================
# Module exports
# ============================================================

__all__ = [
    "execute_step2",
    "_entity_description_task",
    "_facetpoint_extraction_task",
    "_update_entity_descriptions_and_types",
]
