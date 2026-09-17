# m_flow/memory/episodic/episode_builder/step1_facet_prep.py
"""
Step 1: Time Calculation + Facet Preparation

This module implements the facet preparation phase:
1. Step 0: Pre-compute merged_time from episode summary
2. Step 8: Update entity time fields (immediately after Step 0)
3. STEP 1: Process facets (match/create facets from draft)

Phase 4-New-D: Extracted from write_episodic_memories.py

Design:
- All closures are converted to explicit parameters
- Returns Step1Result with all outputs
- Entity time field updates are done in-place (preserves object references)
- Updates dict and existing_by_id are returned for downstream use
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from m_flow.shared.logging_utils import get_logger

# Node ID generation
from m_flow.core.domain.utils.generate_node_id import generate_node_id

# Normalization
from m_flow.memory.episodic.normalization import (
    _nfkc,
    normalize_for_compare,
    normalize_for_id,
    truncate as _truncate,
    evaluate_search_text,
    SearchTextQuality,
)

# Pure functions
from m_flow.memory.episodic.utils.pure_functions import (
    _extract_time_fields_from_episode,
    _choose_better_description,
)

# Data classes
from m_flow.memory.episodic.utils.models import FacetUpdate

# Time utilities
from m_flow.retrieval.time import extract_mentioned_time
from m_flow.memory.episodic.state import merge_episode_times

# Pipeline contexts
from m_flow.memory.episodic.episode_builder.pipeline_contexts import (
    Step1Result,
)

if TYPE_CHECKING:
    from m_flow.core.domain.models import Entity  # Entity is the new name for Entity
    from m_flow.memory.episodic.models import EpisodicWriteDraft
    from m_flow.knowledge.summarization.models import FragmentDigest
    from m_flow.memory.episodic.semantic_merge import SemanticFacetMatcher
    from m_flow.memory.episodic.state import EpisodeState, ExistingFacet


logger = get_logger(__name__)


# ============================================================
# Helper: _get_or_init_update factory
# ============================================================


def _create_update_getter(
    updates: Dict[str, FacetUpdate],
    existing_by_id: Dict[str, "ExistingFacet"],
) -> callable:
    """
    Create a closure for _get_or_init_update function.

    Args:
        updates: Dict to store facet updates
        existing_by_id: Dict of existing facets by ID

    Returns:
        A function that gets or initializes a FacetUpdate
    """

    def _get_or_init_update(facet_id: str) -> FacetUpdate:
        if facet_id in updates:
            return updates[facet_id]
        if facet_id in existing_by_id:
            ex = existing_by_id[facet_id]
            upd = FacetUpdate(
                id=facet_id,
                facet_type=ex.facet_type or "facet",
                search_text=ex.search_text or "",
                description=ex.description,
                aliases=list(ex.aliases or []),
                touched=False,
                # Preserve existing Facet's own time fields (not inherited from Episode)
                mentioned_time_start_ms=ex.mentioned_time_start_ms,
                mentioned_time_end_ms=ex.mentioned_time_end_ms,
                mentioned_time_confidence=ex.mentioned_time_confidence,
                mentioned_time_text=ex.mentioned_time_text,
            )
            updates[facet_id] = upd
            return upd
        upd = FacetUpdate(
            id=facet_id,
            facet_type="facet",
            search_text="",
            description=None,
            aliases=[],
            touched=False,
        )
        updates[facet_id] = upd
        return upd

    return _get_or_init_update


# ============================================================
# Step 0: Time Calculation
# ============================================================


def _calculate_merged_time(
    episode_summary: str,
    doc_summaries: List["FragmentDigest"],
    state: "EpisodeState",
) -> Tuple[Dict[str, Any], int]:
    """
    Calculate merged time from episode summary.

    Args:
        episode_summary: The episode summary text
        doc_summaries: List of document summaries (for anchor_time_ms)
        state: Episode state with existing time info

    Returns:
        Tuple of (merged_time dict, anchor_time_ms)
        merged_time: Dict with mentioned_time_* fields, or empty dict if no time
        anchor_time_ms: Anchor time for parsing relative time expressions
    """
    # Prepare anchor_time_ms
    anchor_time_ms = None
    for ts in doc_summaries:
        ch = ts.made_from
        if hasattr(ch, "created_at") and ch.created_at:
            anchor_time_ms = ch.created_at
            break

    # Pre-extract time
    time_result = extract_mentioned_time(
        text=episode_summary,
        anchor_time_ms=anchor_time_ms,
        min_confidence=0.5,
    )

    # Pre-merge time
    if time_result.has_time:
        merged_time = merge_episode_times(
            existing_state=state,
            new_start_ms=time_result.start_ms,
            new_end_ms=time_result.end_ms,
            new_confidence=time_result.confidence,
            new_text=time_result.evidence_text,
        )
    elif state.has_mentioned_time:
        # New content has no time, but existing episode has time, keep original
        merged_time = {
            "mentioned_time_start_ms": state.mentioned_time_start_ms,
            "mentioned_time_end_ms": state.mentioned_time_end_ms,
            "mentioned_time_confidence": state.mentioned_time_confidence,
            "mentioned_time_text": state.mentioned_time_text,
        }
    else:
        merged_time = {}

    return merged_time, anchor_time_ms


# ============================================================
# Step 8: Update Entity Time Fields
# ============================================================


def _update_entity_time_fields(
    top_entities: List["Entity"],
    merged_time: Dict[str, Any],
    episode_id_str: str,
) -> None:
    """
    Update entity time fields in-place.

    Args:
        top_entities: List of Entity objects to update
        merged_time: Dict with mentioned_time_* fields
        episode_id_str: Episode ID for logging

    Note:
        This modifies top_entities in-place. Since top_entities and entity_map
        share the same object references, changes are visible in both.
    """
    if not merged_time:
        return

    entity_time_fields = _extract_time_fields_from_episode(merged_time)
    for entity in top_entities:
        entity.mentioned_time_start_ms = entity_time_fields.get("mentioned_time_start_ms")
        entity.mentioned_time_end_ms = entity_time_fields.get("mentioned_time_end_ms")
        entity.mentioned_time_confidence = entity_time_fields.get("mentioned_time_confidence")
        entity.mentioned_time_text = entity_time_fields.get("mentioned_time_text")

    logger.info(
        f"[TIME_PROPAGATION] Step 8 completed: updated time fields for {len(top_entities)} Entities, "
        f"entity_names={[e.name[:20] for e in top_entities[:3]]}{'...' if len(top_entities) > 3 else ''}"
    )


# ============================================================
# STEP 1: Process Facets
# ============================================================


async def _process_facets(
    draft: "EpisodicWriteDraft",
    state: "EpisodeState",
    semantic_matcher: "SemanticFacetMatcher",
    episode_id_str: str,
    max_new_facets_per_batch: int,
    enable_semantic_merge: bool,
    anchor_time_ms: int = None,
) -> Tuple[Dict[str, FacetUpdate], Dict[str, "ExistingFacet"]]:
    """
    Process facets from draft: match existing or create new.

    Args:
        draft: Draft with facets from Phase 0A
        state: Episode state with existing facets
        semantic_matcher: Prepared semantic matcher
        episode_id_str: Episode ID for generating facet IDs
        max_new_facets_per_batch: Maximum new facets to process
        enable_semantic_merge: Whether to enable semantic matching
        anchor_time_ms: Anchor time for parsing relative time in facet description

    Returns:
        Tuple of (updates dict, existing_by_id dict)
    """
    # lookup: (facet_type, normalized_text) -> facet_id
    lookup: Dict[Tuple[str, str], str] = {}
    existing_by_id: Dict[str, "ExistingFacet"] = {f.id: f for f in state.facets}

    for f in state.facets:
        ft = f.facet_type or "facet"
        lookup[(ft, normalize_for_compare(f.search_text))] = f.id
        for a in f.aliases or []:
            lookup[(ft, normalize_for_compare(a))] = f.id

    # working updates
    updates: Dict[str, FacetUpdate] = {}
    _get_or_init_update = _create_update_getter(updates, existing_by_id)

    # Process new facet candidates
    for f in (draft.facets or [])[:max_new_facets_per_batch]:
        facet_type = _nfkc(f.facet_type or "facet") or "facet"
        st = _nfkc(f.search_text or "")

        # Evaluate search text quality
        st_eval = evaluate_search_text(st)

        # CRITICAL: Discard invalid text
        if st_eval.quality == SearchTextQuality.CRITICAL:
            logger.debug(
                f"[episodic] Facet skipped (CRITICAL): search_text='{_truncate(st, 30)}', reason={st_eval.reason}"
            )
            continue

        # WARNING: Log warning but keep
        if st_eval.should_warn:
            logger.warning(
                f"[episodic] Low-quality facet (WARNING): search_text='{st}', "
                f"reason={st_eval.reason} - keeping but may affect retrieval quality"
            )

        st_norm = normalize_for_compare(st)

        # string match
        matched_id = lookup.get((facet_type, st_norm), None)

        # semantic match if not string match
        if not matched_id and enable_semantic_merge:
            matched_id = await semantic_matcher.match(candidate_text=st, candidate_type=facet_type)

        if matched_id:
            # absorb into existing facet
            upd = _get_or_init_update(matched_id)

            # Only update lookup to support search_text deduplication matching
            lookup[(facet_type, st_norm)] = matched_id

            # description merge (preserve)
            new_desc = _choose_better_description(upd.description, f.description)
            if new_desc != upd.description:
                upd.description = new_desc
                upd.touched = True

            continue

        # new facet
        facet_id = str(generate_node_id(f"Facet:{episode_id_str}:{facet_type}:{normalize_for_id(st)}"))

        facet_desc = (f.description or "").strip() or None

        # Extract Facet's own time from its description (independent of Episode time)
        facet_time_start_ms = None
        facet_time_end_ms = None
        facet_time_confidence = None
        facet_time_text = None

        if facet_desc:
            facet_time_result = extract_mentioned_time(
                text=facet_desc,
                anchor_time_ms=anchor_time_ms,
                min_confidence=0.5,
            )
            if facet_time_result.has_time:
                facet_time_start_ms = facet_time_result.start_ms
                facet_time_end_ms = facet_time_result.end_ms
                facet_time_confidence = facet_time_result.confidence
                facet_time_text = facet_time_result.evidence_text
                logger.debug(
                    f"[TIME_PROPAGATION] Facet time extracted: facet={facet_id[:12]}..., "
                    f"start={facet_time_start_ms}, end={facet_time_end_ms}, "
                    f"text='{facet_time_text[:30] if facet_time_text else ''}'"
                )

        upd = FacetUpdate(
            id=facet_id,
            facet_type=facet_type,
            search_text=st,
            description=facet_desc,
            aliases=[],
            touched=True,
            # Facet's own time fields
            mentioned_time_start_ms=facet_time_start_ms,
            mentioned_time_end_ms=facet_time_end_ms,
            mentioned_time_confidence=facet_time_confidence,
            mentioned_time_text=facet_time_text,
        )

        # NOTE: aliases generation is disabled
        upd.aliases = []

        updates[facet_id] = upd
        lookup[(facet_type, st_norm)] = facet_id

    logger.info(f"[episodic] Facets prepared for processing: {len(updates)} facets in updates dict")

    return updates, existing_by_id


# ============================================================
# Main Execution Function
# ============================================================


async def execute_step1(
    episode_id_str: str,
    episode_summary: str,
    doc_summaries: List["FragmentDigest"],
    state: "EpisodeState",
    top_entities: List["Entity"],
    draft: "EpisodicWriteDraft",
    semantic_matcher: "SemanticFacetMatcher",
    episode_name: str,
    episode_signature: str,
    max_new_facets_per_batch: int,
    enable_semantic_merge: bool,
    evidence_chunks_per_facet: int,
) -> Step1Result:
    """
    Execute Step 1: Time calculation + Facet preparation.

    This step:
    1. Calculates merged_time from episode summary (Step 0)
    2. Updates entity time fields in-place (Step 8)
    3. Processes facets from draft (STEP 1)
    4. Collects evidence pairs for downstream use

    Args:
        episode_id_str: Episode identifier
        episode_summary: The episode summary text (from draft or computed)
        doc_summaries: List of document summaries
        state: Episode state from database
        top_entities: List of Entity objects (will be modified in-place)
        draft: Draft with facets from Phase 0A
        semantic_matcher: Prepared semantic matcher from Phase 0A
        episode_name: Episode name (from draft or state)
        episode_signature: Episode signature (from draft or state)
        max_new_facets_per_batch: Maximum new facets to process
        enable_semantic_merge: Whether to enable semantic matching
        evidence_chunks_per_facet: Number of evidence chunks per facet

    Returns:
        Step1Result containing:
        - episode_name, episode_signature, episode_summary
        - merged_time: Dict with mentioned_time_* fields
        - updates: Dict of facet_id -> FacetUpdate
        - existing_by_id: Dict of facet_id -> ExistingFacet
        - evidence_pairs: List of (chunk, summary_text) pairs

    Note:
        top_entities are modified in-place with time fields. Since they share
        object references with entity_map, changes are visible in both.
    """
    # Step 0: Calculate merged_time and get anchor_time_ms for Facet time extraction
    merged_time, anchor_time_ms = _calculate_merged_time(
        episode_summary=episode_summary,
        doc_summaries=doc_summaries,
        state=state,
    )

    # Log time calculation result
    if merged_time and merged_time.get("mentioned_time_start_ms"):
        conf = merged_time.get("mentioned_time_confidence")
        conf_str = f"{conf:.2f}" if conf is not None else "N/A"
        logger.info(
            f"[TIME_PROPAGATION] Step 0 completed: episode={episode_id_str[:12]}..., "
            f"has_time=True, "
            f"start={merged_time.get('mentioned_time_start_ms')}, "
            f"end={merged_time.get('mentioned_time_end_ms')}, "
            f"conf={conf_str}, "
            f"evidence='{(merged_time.get('mentioned_time_text') or '')[:50]}'"
        )
    else:
        logger.debug(f"[TIME_PROPAGATION] Step 0: episode={episode_id_str[:12]}... no time info")

    # Step 8: Update entity time fields (in-place)
    _update_entity_time_fields(
        top_entities=top_entities,
        merged_time=merged_time,
        episode_id_str=episode_id_str,
    )

    # STEP 1: Process facets (with anchor_time_ms for individual Facet time extraction)
    updates, existing_by_id = await _process_facets(
        draft=draft,
        state=state,
        semantic_matcher=semantic_matcher,
        episode_id_str=episode_id_str,
        max_new_facets_per_batch=max_new_facets_per_batch,
        enable_semantic_merge=enable_semantic_merge,
        anchor_time_ms=anchor_time_ms,
    )

    # Collect evidence pairs
    evidence_pairs: List[Tuple[Any, str]] = []
    for ts in doc_summaries[-max(1, evidence_chunks_per_facet) :]:
        ch = ts.made_from
        summary_text = getattr(ts, "text", "") or ""
        evidence_pairs.append((ch, summary_text))

    return Step1Result(
        episode_name=episode_name,
        episode_signature=episode_signature,
        episode_summary=episode_summary,
        merged_time=merged_time if merged_time else None,
        updates=updates,
        existing_by_id=existing_by_id,
        evidence_pairs=evidence_pairs,
    )


# ============================================================
# Module exports
# ============================================================

__all__ = [
    "execute_step1",
    "_calculate_merged_time",
    "_update_entity_time_fields",
    "_process_facets",
]
