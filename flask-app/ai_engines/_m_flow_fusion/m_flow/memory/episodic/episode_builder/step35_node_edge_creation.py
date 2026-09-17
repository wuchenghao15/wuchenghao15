# m_flow/memory/episodic/episode_builder/step35_node_edge_creation.py
"""
Step 3-5: Node and Edge Creation

This module implements the node and edge creation phase:
1. Build has_facet_edges (Facet objects with FacetPoints)
2. Build involves_entity_edges
3. Queue Facet-Entity edges
4. Collect same_entity_as edges
5. Build includes_chunk_edges
6. Create Episode object

Phase 4-New-F: Extracted from write_episodic_memories.py

Design:
- This is the most complex step, handling multiple edge types
- Uses pending edge queues (context_vars) for deferred insertion
- Maintains time propagation logic throughout
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from m_flow.shared.logging_utils import get_logger

# Node ID generation
from m_flow.core.domain.utils.generate_node_id import generate_node_id

# Domain models
from m_flow.core import Edge
from m_flow.core.domain.models import (
    Entity,
    Episode,
    Facet,
    FacetPoint,
)  # Entity is new, Entity is alias

# Normalization
from m_flow.memory.episodic.normalization import (
    _nfkc,
    normalize_for_compare,
    normalize_for_id,
)

# Pure functions
from m_flow.memory.episodic.utils.pure_functions import (
    _extract_time_fields_from_episode,
    ensure_nodeset,
)

# Edge text generators
from m_flow.memory.episodic.edge_text_generators import (
    make_has_facet_edge_text as _make_has_facet_edge_text,
    make_involves_entity_edge_text as _make_involves_entity_edge_text,
    make_same_entity_as_edge_text as _make_same_entity_as_edge_text,
    make_supported_by_edge_text as _make_supported_by_edge_text,
    make_includes_chunk_edge_text as _make_includes_chunk_edge_text,
    make_has_point_edge_text as _make_has_point_edge_text,
    make_facet_involves_entity_edge_text,
)

# Context vars for pending edges
from m_flow.memory.episodic.context_vars import (
    _add_pending_same_entity_edge,
    _add_pending_facet_entity_edge,
)

# Facet-Entity matching
from m_flow.memory.episodic.facet_entity_matcher import match_entities_to_facets

# Aliases filter
from m_flow.memory.episodic.aliases import is_bad_alias

if TYPE_CHECKING:
    from m_flow.core import NodeSet
    from m_flow.memory.episodic.models import FacetPointDraft
    from m_flow.memory.episodic.utils.models import FacetUpdate
    from m_flow.memory.episodic.state import ExistingFacet


logger = get_logger(__name__)


# ============================================================
# Build has_facet_edges
# ============================================================


def _build_has_facet_edges(
    updates: Dict[str, "FacetUpdate"],
    existing_by_id: Dict[str, "ExistingFacet"],
    facet_points_cache: Dict[str, List["FacetPointDraft"]],
    evidence_pairs: List[Tuple[Any, str]],
    merged_time: Optional[Dict[str, Any]],
    episode_time_fields: Dict[str, Any],
    episodic_nodeset: "NodeSet",
    enable_facet_points: bool,
    dataset_id: Optional[str] = None,
) -> List[Tuple[Edge, Facet]]:
    """
    Build has_facet edges with Facet objects.

    Args:
        updates: Dict of facet_id -> FacetUpdate
        existing_by_id: Dict of facet_id -> ExistingFacet
        facet_points_cache: Dict of facet_id -> list of FacetPointDraft
        evidence_pairs: List of (chunk, summary_text) pairs
        merged_time: Merged time info dict
        episode_time_fields: Extracted time fields for episode
        episodic_nodeset: NodeSet for memory_spaces
        enable_facet_points: Whether FacetPoints are enabled
        dataset_id: Dataset ID for isolation (prevents cross-dataset merging)

    Returns:
        List of (Edge, Facet) tuples for has_facet relationship
    """
    has_facet_edges: List[Tuple[Edge, Facet]] = []

    # Extract earliest created_at from evidence_pairs for Facet inheritance
    # Priority: 1. Document.created_at (from API created_at parameter)
    #           2. ContentFragment.created_at (default: current system time)
    earliest_chunk_created_at = None
    if evidence_pairs:
        for ch, _ in evidence_pairs:
            # Priority 1: Try Document.created_at (preserves API-provided historical timestamp)
            doc_created_at = None
            if hasattr(ch, "is_part_of") and ch.is_part_of:
                doc_created_at = getattr(ch.is_part_of, "created_at", None)

            # Priority 2: Fall back to ContentFragment.created_at
            ch_created_at = doc_created_at or getattr(ch, "created_at", None)

            if ch_created_at is not None:
                if earliest_chunk_created_at is None or ch_created_at < earliest_chunk_created_at:
                    earliest_chunk_created_at = ch_created_at

    for upd in updates.values():
        # Step 7: Force update existing child node time fields
        should_force_update_time = False
        if not upd.touched and upd.id in existing_by_id:
            if merged_time and any(
                [
                    merged_time.get("mentioned_time_start_ms"),
                    merged_time.get("mentioned_time_end_ms"),
                ]
            ):
                should_force_update_time = True
                logger.debug(
                    f"[episodic] Step 7: Force updating Facet {upd.id} time fields "
                    f"due to Episode time update (touched=False)"
                )
            else:
                continue

        # Prepare time fields: prioritize Facet's own time, fallback to Episode time
        # This ensures Facets preserve their individual time fields during merge
        if upd.mentioned_time_start_ms is not None:
            # Use Facet's own time fields (extracted from its description)
            facet_time_fields = {
                "mentioned_time_start_ms": upd.mentioned_time_start_ms,
                "mentioned_time_end_ms": upd.mentioned_time_end_ms,
                "mentioned_time_confidence": upd.mentioned_time_confidence,
                "mentioned_time_text": upd.mentioned_time_text,
            }
            logger.debug(
                f"[TIME_PROPAGATION] Using Facet's own time: facet={upd.id[:12]}..., "
                f"start={upd.mentioned_time_start_ms}"
            )
        else:
            # Fallback to Episode time (for Facets without explicit time in description)
            facet_time_fields = _extract_time_fields_from_episode(merged_time) if merged_time else {}

        if earliest_chunk_created_at is not None:
            facet_time_fields["created_at"] = earliest_chunk_created_at

        if facet_time_fields and facet_time_fields.get("mentioned_time_start_ms"):
            logger.debug(
                f"[TIME_PROPAGATION] Facet preparation: facet={upd.id[:12]}..., "
                f"has_time=True, force_update={should_force_update_time}"
            )

        # Aliases disabled
        cleaned = None
        aliases_text = None

        # FacetPoint extraction
        has_point_edges: Optional[List[Tuple[Edge, FacetPoint]]] = None
        facet_desc = upd.description.strip() if upd.description else None
        facet_anchor_text = facet_desc

        if enable_facet_points and facet_desc:
            extracted = facet_points_cache.get(upd.id, [])

            _debug_extracted_count = len(extracted)
            _debug_filtered_reasons: Dict[str, int] = {
                "empty": 0,
                "bad_alias": 0,
                "duplicate": 0,
                "same_as_facet": 0,
            }

            seen_norm = set()
            for p in extracted:
                stp = _nfkc(getattr(p, "search_text", "") or "")
                if not stp:
                    _debug_filtered_reasons["empty"] += 1
                    continue

                if is_bad_alias(stp, max_len=0):
                    _debug_filtered_reasons["bad_alias"] += 1
                    logger.warning(
                        f"[episodic] FacetPoint filtered (bad_alias): len={len(stp)}, text='{stp[:80]}...'"
                        if len(stp) > 80
                        else f"[episodic] FacetPoint filtered (bad_alias): len={len(stp)}, text='{stp}'"
                    )
                    continue

                k = normalize_for_compare(stp)
                if k in seen_norm:
                    _debug_filtered_reasons["duplicate"] += 1
                    continue

                if k == normalize_for_compare(upd.search_text):
                    _debug_filtered_reasons["same_as_facet"] += 1
                    logger.debug(f"[episodic] FacetPoint filtered (same_as_facet): '{stp}' == '{upd.search_text}'")
                    continue

                seen_norm.add(k)

                point_id = str(generate_node_id(f"FacetPoint:{upd.id}:{normalize_for_id(stp)}"))

                # Step 3: FacetPoint time fields
                point_time_fields = facet_time_fields if facet_time_fields else episode_time_fields

                point_dp = FacetPoint(
                    id=point_id,
                    name=stp,
                    search_text=stp,
                    aliases=None,
                    aliases_text=None,
                    description=getattr(p, "description", None),
                    memory_spaces=[episodic_nodeset],
                    **point_time_fields,
                )

                if point_time_fields and point_time_fields.get("mentioned_time_start_ms"):
                    logger.debug(
                        f"[TIME_PROPAGATION] Step 3: FacetPoint created point={point_id[:12]}..., has_time=True"
                    )

                if has_point_edges is None:
                    has_point_edges = []

                has_point_edges.append(
                    (
                        Edge(
                            relationship_type="has_point",
                            edge_text=_make_has_point_edge_text(
                                facet_type=upd.facet_type,
                                facet_search_text=upd.search_text,
                                point_search_text=stp,
                                point_description=getattr(p, "description", "") or "",
                            ),
                        ),
                        point_dp,
                    )
                )

            if _debug_extracted_count > 0:
                _built_count = len(has_point_edges) if has_point_edges else 0
                if _built_count < _debug_extracted_count:
                    logger.warning(
                        f"[episodic] FacetPoint FILTER STATS: facet='{upd.search_text}', "
                        f"extracted={_debug_extracted_count}, built={_built_count}, "
                        f"filtered={_debug_filtered_reasons}"
                    )

            logger.info(
                f"[episodic] FacetPoint built: facet='{upd.search_text}', "
                f"points={len(has_point_edges) if has_point_edges else 0}"
            )

        # Create Facet object
        if should_force_update_time:
            existing_facet = existing_by_id.get(upd.id)
            if not existing_facet:
                logger.error(
                    f"[episodic] Step 7: Unexpected state - should_force_update_time=True "
                    f"but upd.id={upd.id} not in existing_by_id, skipping"
                )
                continue

            facet_dp = Facet(
                id=upd.id,
                name=existing_facet.search_text or upd.search_text,
                facet_type=existing_facet.facet_type or upd.facet_type,
                search_text=existing_facet.search_text or upd.search_text,
                aliases=list(existing_facet.aliases) if existing_facet.aliases else None,
                aliases_text=None,
                description=existing_facet.description or upd.description,
                anchor_text=None,
                memory_spaces=[episodic_nodeset],
                dataset_id=dataset_id,
                **facet_time_fields,
            )
            logger.info(
                f"[TIME_PROPAGATION] Step 7 completed: Facet force update facet={upd.id[:12]}..., "
                f"search_text='{upd.search_text[:30]}...'"
            )
        else:
            facet_dp = Facet(
                id=upd.id,
                name=upd.search_text,
                facet_type=upd.facet_type,
                search_text=upd.search_text,
                aliases=cleaned or None,
                aliases_text=aliases_text,
                description=facet_desc,
                anchor_text=facet_anchor_text,
                has_point=has_point_edges,
                memory_spaces=[episodic_nodeset],
                dataset_id=dataset_id,
                supported_by=[
                    (
                        Edge(
                            relationship_type="supported_by",
                            edge_text=_make_supported_by_edge_text(
                                facet_search_text=upd.search_text,
                                chunk_id=str(ch.id),
                                chunk_index=int(getattr(ch, "chunk_index", -1)),
                                chunk_summary=summary_text,
                            ),
                        ),
                        ch,
                    )
                    for (ch, summary_text) in evidence_pairs
                ]
                if evidence_pairs
                else None,
                **facet_time_fields,
            )

            if facet_time_fields and facet_time_fields.get("mentioned_time_start_ms"):
                logger.debug(
                    f"[TIME_PROPAGATION] Step 2 completed: Facet created facet={upd.id[:12]}..., "
                    f"search_text='{upd.search_text[:30]}...', has_time=True"
                )

        has_facet_edges.append(
            (
                Edge(
                    relationship_type="has_facet",
                    edge_text=_make_has_facet_edge_text(
                        facet_type=upd.facet_type,
                        facet_search_text=upd.search_text,
                        facet_description=facet_desc,
                    ),
                ),
                facet_dp,
            )
        )

    return has_facet_edges


# ============================================================
# Build involves_entity_edges
# ============================================================


def _build_involves_entity_edges(
    entity_context_map: Dict[str, Tuple[str, str]],
    entity_map: Dict[str, Entity],
    top_entities: List[Entity],
    episodic_nodeset: "NodeSet",
    max_entities_per_episode: int,
) -> Tuple[List[Tuple[Edge, Entity]], List[Entity]]:
    """
    Build involves_entity edges.

    Args:
        entity_context_map: Dict mapping entity_name to (description, entity_type)
        entity_map: Dict mapping entity_name to Entity
        top_entities: List of all Entity objects
        episodic_nodeset: NodeSet for memory_spaces
        max_entities_per_episode: Maximum entities to include (0 = unlimited)

    Returns:
        Tuple of (involves_entity_edges, involves_entities list)
    """
    involves_entities: List[Entity] = []
    for entity_name in entity_context_map:
        if entity_name in entity_map:
            involves_entities.append(entity_map[entity_name])
        else:
            for e in top_entities:
                if e.name == entity_name:
                    involves_entities.append(e)
                    break

    if max_entities_per_episode > 0:
        involves_entities = involves_entities[:max_entities_per_episode]

    for e in involves_entities:
        ensure_nodeset(e, episodic_nodeset)

    def _get_entity_description(name: str) -> str:
        info = entity_context_map.get(name, "")
        if isinstance(info, tuple):
            return info[0]
        return info

    involves_entity_edges: List[Tuple[Edge, Entity]] = [
        (
            Edge(
                relationship_type="involves_entity",
                edge_text=_make_involves_entity_edge_text(e, _get_entity_description(e.name)),
            ),
            e,
        )
        for e in involves_entities
    ]

    return involves_entity_edges, involves_entities


# ============================================================
# Queue Facet-Entity edges
# ============================================================


def _queue_facet_entity_edges(
    updates: Dict[str, "FacetUpdate"],
    involves_entities: List[Entity],
    entity_map: Dict[str, Entity],
    entity_context_map: Dict[str, Tuple[str, str]],
) -> int:
    """
    Match entities to facets and queue Facet-Entity edges.

    Args:
        updates: Dict of facet_id -> FacetUpdate
        involves_entities: List of involved Entity objects
        entity_map: Dict mapping entity_name to Entity
        entity_context_map: Dict mapping entity_name to (description, entity_type)

    Returns:
        Number of edges queued
    """
    episode_facets = list(updates.values())
    entity_names_for_matching = [e.name for e in involves_entities]

    def _get_entity_description(name: str) -> str:
        info = entity_context_map.get(name, "")
        if isinstance(info, tuple):
            return info[0]
        return info

    entity_desc_for_matching: Dict[str, str] = {}
    for e in involves_entities:
        entity_desc_for_matching[e.name] = _get_entity_description(e.name)

    edges_queued = 0
    if episode_facets and entity_names_for_matching:
        entity_to_facets = match_entities_to_facets(
            entity_names=entity_names_for_matching,
            facets=episode_facets,
        )

        for entity_name, facet_matches in entity_to_facets.items():
            entity_obj = entity_map.get(entity_name)
            if not entity_obj:
                continue

            entity_desc = entity_desc_for_matching.get(entity_name, "")

            for match in facet_matches:
                facet_id = match["facet_id"]
                facet_search_text = match["facet_search_text"]

                edge_text = make_facet_involves_entity_edge_text(
                    entity_name=entity_name,
                    entity_description=entity_desc,
                    facet_search_text=facet_search_text,
                )

                edge_data = {
                    "source_id": str(facet_id),
                    "target_id": str(entity_obj.id),
                    "relationship_name": "involves_entity",
                    "edge_text": edge_text,
                }
                _add_pending_facet_entity_edge(edge_data)
                edges_queued += 1

        logger.debug(
            f"[episodic] Matched {len(entity_to_facets)} entities to facets, queued {edges_queued} Facet-Entity edges"
        )

    return edges_queued


# ============================================================
# Collect same_entity_as edges
# ============================================================


def _collect_same_entity_as_edges(
    same_entity_edges_pending: List[Tuple[Entity, List[Dict[str, Any]]]],
    involves_entities: List[Entity],
    entity_map: Dict[str, Entity],
) -> int:
    """
    Collect same_entity_as edges and add to pending queue.

    Args:
        same_entity_edges_pending: List of (new_entity, existing_list) pairs
        involves_entities: List of involved Entity objects
        entity_map: Dict mapping entity_name to Entity

    Returns:
        Number of edges added to pending queue
    """
    involves_entity_names = {e.name for e in involves_entities}
    edges_added = 0

    for new_entity, existing_list in same_entity_edges_pending:
        if new_entity.name not in involves_entity_names:
            continue

        actual_entity = entity_map.get(new_entity.name, new_entity)

        for existing in existing_list:
            edge_text = _make_same_entity_as_edge_text(
                actual_entity,
                Entity(
                    id=existing["id"],
                    name=existing["name"],
                    description=existing.get("description", ""),
                    canonical_name=existing.get("canonical_name", ""),
                    memory_type=existing.get("memory_type"),
                ),
            )
            edge_data = {
                "source_id": str(actual_entity.id),
                "target_id": str(existing["id"]),
                "relationship_name": "same_entity_as",
                "edge_text": edge_text,
            }
            _add_pending_same_entity_edge(edge_data)
            edges_added += 1

    return edges_added


# ============================================================
# Build includes_chunk_edges
# ============================================================


def _build_includes_chunk_edges(
    doc_summaries: List[Any],
) -> List[Tuple[Edge, Any]]:
    """
    Build includes_chunk edges.

    Args:
        doc_summaries: List of document summaries

    Returns:
        List of (Edge, chunk) tuples
    """
    includes_chunk_edges: List[Tuple[Edge, Any]] = []
    for ts in doc_summaries:
        ch = ts.made_from
        includes_chunk_edges.append(
            (
                Edge(
                    relationship_type="includes_chunk",
                    edge_text=_make_includes_chunk_edge_text(
                        chunk_id=str(ch.id),
                        chunk_index=int(getattr(ch, "chunk_index", -1)),
                    ),
                ),
                ch,
            )
        )
    return includes_chunk_edges


# ============================================================
# Create Episode object
# ============================================================


def _create_episode(
    episode_id_str: str,
    episode_name: str,
    episode_summary: str,
    episode_signature: str,
    has_facet_edges: List[Tuple[Edge, Facet]],
    involves_entity_edges: List[Tuple[Edge, Entity]],
    includes_chunk_edges: List[Tuple[Edge, Any]],
    episodic_nodeset: "NodeSet",
    episode_memory_types: Dict[str, str],
    routing_decisions: Dict[str, str],
    state_exists: bool,
    state_memory_type: Optional[str],
    merged_time: Optional[Dict[str, Any]],
    dataset_id: Optional[str] = None,
    created_at: Optional[int] = None,
) -> Episode:
    """
    Create Episode object.

    Args:
        episode_id_str: Episode identifier
        episode_name: Episode name
        episode_summary: Episode summary
        episode_signature: Episode signature
        has_facet_edges: List of (Edge, Facet) tuples
        involves_entity_edges: List of (Edge, Entity) tuples
        includes_chunk_edges: List of (Edge, chunk) tuples
        episodic_nodeset: NodeSet for memory_spaces
        episode_memory_types: Dict mapping episode_id to memory_type
        routing_decisions: Dict mapping episode_id to routing decision
        state_exists: Whether the episode already exists
        state_memory_type: Existing episode's memory_type
        merged_time: Merged time info dict
        dataset_id: Dataset ID for isolation (prevents cross-dataset merging)

    Returns:
        Episode object
    """
    episode_memory_type = episode_memory_types.get(episode_id_str, "episodic")

    routing_decision = routing_decisions.get(episode_id_str, "new")
    if routing_decision == "existing" and state_exists:
        if state_memory_type:
            episode_memory_type = state_memory_type

    episode_dp = Episode(
        id=episode_id_str,
        name=episode_name,
        summary=episode_summary,
        signature=episode_signature,
        memory_spaces=[episodic_nodeset],
        has_facet=has_facet_edges or None,
        involves_entity=involves_entity_edges or None,
        includes_chunk=includes_chunk_edges or None,
        memory_type=episode_memory_type,
        dataset_id=dataset_id,
        mentioned_time_start_ms=merged_time.get("mentioned_time_start_ms") if merged_time else None,
        mentioned_time_end_ms=merged_time.get("mentioned_time_end_ms") if merged_time else None,
        mentioned_time_confidence=merged_time.get("mentioned_time_confidence") if merged_time else None,
        mentioned_time_text=merged_time.get("mentioned_time_text") if merged_time else None,
    )

    # Set created_at from source content (preserves historical timestamp)
    if created_at is not None:
        episode_dp.created_at = created_at

    if merged_time and merged_time.get("mentioned_time_start_ms"):
        facet_count = len(has_facet_edges) if has_facet_edges else 0
        entity_count = len(involves_entity_edges) if involves_entity_edges else 0
        logger.info(
            f"[TIME_PROPAGATION] Episode complete: episode={episode_id_str[:12]}..., "
            f"name='{episode_name[:30]}...', has_time=True, "
            f"facets={facet_count}, entities={entity_count}"
        )

    return episode_dp


# ============================================================
# Module exports
# ============================================================

__all__ = [
    "_build_has_facet_edges",
    "_build_involves_entity_edges",
    "_queue_facet_entity_edges",
    "_collect_same_entity_as_edges",
    "_build_includes_chunk_edges",
    "_create_episode",
]
