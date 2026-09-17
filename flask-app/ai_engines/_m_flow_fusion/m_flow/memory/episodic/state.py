# m_flow/memory/episodic/state.py
"""
Episode State Fetching

Fetch existing episode state from graph before writing:
- title/name, signature (prevent drift)
- Existing facets list (prevent duplicates)
- Existing involves_entity entity name list (maintain stable anchors)

Enhancements:
- mentioned_time_* fields (event occurrence time)
- merge_episode_times: Merge old and new time ranges
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel

from m_flow.shared.logging_utils import get_logger
from m_flow.memory.episodic.normalization import normalize_for_compare
from m_flow.retrieval.time import validate_time_range

logger = get_logger("episodic.state")


class ExistingFacet(BaseModel):
    """Existing Facet information (for deduplication during incremental updates)."""

    id: str
    facet_type: Optional[str] = None
    search_text: Optional[str] = None
    description: Optional[str] = None
    aliases: List[str] = []
    # Facet's own time fields (independent of Episode time)
    mentioned_time_start_ms: Optional[int] = None
    mentioned_time_end_ms: Optional[int] = None
    mentioned_time_confidence: Optional[float] = None
    mentioned_time_text: Optional[str] = None


class ExistingEntity(BaseModel):
    """Existing Entity/Entity information (for description merging during incremental updates)."""

    id: str
    name: str
    description: Optional[str] = None
    merge_count: int = 0  # Number of times this entity has been merged


class EpisodeState(BaseModel):
    """Current state of Episode (for incremental updates)."""

    episode_id: str
    exists: bool = False  # Whether already exists in database
    title: Optional[str] = None
    signature: Optional[str] = None
    summary: Optional[str] = None
    memory_type: Optional[str] = None  # "episodic" | "atomic" | None
    facets: List[ExistingFacet] = []
    entity_names: List[str] = []  # Name-only view (parallel to .entities)
    entities: List[ExistingEntity] = []  # New: entities with descriptions

    # Time enhancement: event occurrence time
    mentioned_time_start_ms: Optional[int] = None
    mentioned_time_end_ms: Optional[int] = None
    mentioned_time_confidence: Optional[float] = None
    mentioned_time_text: Optional[str] = None

    @property
    def has_mentioned_time(self) -> bool:
        """Whether has valid event time."""
        return self.mentioned_time_start_ms is not None and self.mentioned_time_end_ms is not None


async def fetch_episode_state(graph_engine, episode_id: str) -> EpisodeState:
    """
    Fetch current state of Episode from graph database.

    Args:
        graph_engine: Graph database engine
        episode_id: Episode node ID

    Returns:
        EpisodeState: Contains exists, title, signature, summary, memory_type, facets, entity_names, mentioned_time_*
    """
    exists = False
    title = None
    signature = None
    summary = None
    memory_type = None
    # mentioned_time fields
    mentioned_time_start_ms = None
    mentioned_time_end_ms = None
    mentioned_time_confidence = None
    mentioned_time_text = None

    # Try to get Episode node
    try:
        node = await graph_engine.get_node(episode_id)
        if node and isinstance(node, dict):
            exists = True
            title = node.get("name")
            signature = node.get("signature")
            summary = node.get("summary")
            memory_type = node.get("memory_type")
            # Read time fields
            mentioned_time_start_ms = node.get("mentioned_time_start_ms")
            mentioned_time_end_ms = node.get("mentioned_time_end_ms")
            mentioned_time_confidence = node.get("mentioned_time_confidence")
            mentioned_time_text = node.get("mentioned_time_text")
    except Exception as e:
        logger.debug(f"No episode node found for {episode_id}: {e}")

    facets: List[ExistingFacet] = []
    entity_names: List[str] = []
    entities: List[ExistingEntity] = []

    # Get Episode edges
    try:
        # KuzuAdapter.get_edges: returns (source_node_dict, relationship_name, target_node_dict)
        edges = await graph_engine.get_edges(episode_id)
        for _src, rel, dst in edges:  # _src unused but required for unpacking
            dst_type = dst.get("type") if isinstance(dst, dict) else None

            if rel == "has_facet" and dst_type == "Facet":
                facets.append(
                    ExistingFacet(
                        id=str(dst.get("id")),
                        facet_type=dst.get("facet_type"),
                        search_text=dst.get("search_text") or dst.get("name"),
                        description=dst.get("description"),
                        aliases=dst.get("aliases") or [],
                        # Facet's own time fields
                        mentioned_time_start_ms=dst.get("mentioned_time_start_ms"),
                        mentioned_time_end_ms=dst.get("mentioned_time_end_ms"),
                        mentioned_time_confidence=dst.get("mentioned_time_confidence"),
                        mentioned_time_text=dst.get("mentioned_time_text"),
                    )
                )

            if rel == "involves_entity" and dst_type in ("Entity", "Entity"):
                name = dst.get("name")
                if name:
                    entity_names.append(name)
                    # Also capture full entity info for description merging
                    entities.append(
                        ExistingEntity(
                            id=str(dst.get("id")),
                            name=name,
                            description=dst.get("description"),
                            merge_count=dst.get("merge_count", 0) or 0,
                        )
                    )
    except Exception as e:
        logger.debug(f"Failed to get edges for episode {episode_id}: {e}")

    # Deduplicate while preserving order
    # Note: entity_names and entities are parallel lists (same length, same order)
    seen = set()
    uniq_entities = []
    uniq_entity_objs: List[ExistingEntity] = []
    for i in range(len(entity_names)):
        n = entity_names[i]
        if n in seen:
            continue
        seen.add(n)
        uniq_entities.append(n)
        if i < len(entities):
            uniq_entity_objs.append(entities[i])

    return EpisodeState(
        episode_id=episode_id,
        exists=exists,
        title=title,
        signature=signature,
        summary=summary,
        memory_type=memory_type,
        facets=facets,
        entity_names=uniq_entities,
        entities=uniq_entity_objs,
        # Time fields
        mentioned_time_start_ms=mentioned_time_start_ms,
        mentioned_time_end_ms=mentioned_time_end_ms,
        mentioned_time_confidence=mentioned_time_confidence,
        mentioned_time_text=mentioned_time_text,
    )


# ============================================================
# FacetPoint State Query
# ============================================================


class ExistingFacetPoint(BaseModel):
    """Existing FacetPoint information (for deduplication during incremental updates)."""

    id: str
    search_text: str
    aliases: List[str] = []
    description: Optional[str] = None


async def fetch_facet_points(graph_engine, facet_id: str) -> List[ExistingFacetPoint]:
    """
    Read existing FacetPoints for a Facet from graph (Facet --has_point--> FacetPoint).
    Used for cross-batch deduplication/incremental supplementation.

    Args:
        graph_engine: Graph database engine
        facet_id: Facet node ID

    Returns:
        Deduplicated FacetPoint list
    """
    out: List[ExistingFacetPoint] = []
    try:
        edges = await graph_engine.get_edges(facet_id)
        for _, rel, dst in edges:
            if rel != "has_point":
                continue
            if not isinstance(dst, dict):
                continue
            if (dst.get("type") or "") != "FacetPoint":
                continue

            st = str(dst.get("search_text") or dst.get("name") or "")
            aliases = dst.get("aliases") or []
            if not isinstance(aliases, list):
                aliases = []
            desc = dst.get("description")

            if st.strip():
                out.append(
                    ExistingFacetPoint(
                        id=str(dst.get("id") or ""),
                        search_text=st,
                        aliases=[str(x) for x in aliases if x],
                        description=str(desc) if desc is not None else None,
                    )
                )
    except Exception as e:
        logger.debug(f"fetch_facet_points failed for facet={facet_id}: {e}")
        return []

    # Deduplicate (by normalized search_text)
    seen = set()
    uniq: List[ExistingFacetPoint] = []
    for p in out:
        k = normalize_for_compare(p.search_text)
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(p)
    return uniq


# ============================================================
# Time Merge Utility Functions
# ============================================================


def merge_episode_times(
    existing_state: EpisodeState,
    new_start_ms: Optional[int],
    new_end_ms: Optional[int],
    new_confidence: Optional[float],
    new_text: Optional[str],
) -> dict:
    """
    Merge existing Episode time range with newly extracted time range.

    Strategy:
    - Take union of time ranges
    - Weighted average for confidence
    - Merge evidence text

    Args:
        existing_state: Existing Episode state
        new_start_ms: Newly extracted time start
        new_end_ms: Newly extracted time end
        new_confidence: Newly extracted confidence
        new_text: Newly extracted evidence text

    Returns:
        Merged time fields dictionary:
        {
            "mentioned_time_start_ms": ...,
            "mentioned_time_end_ms": ...,
            "mentioned_time_confidence": ...,
            "mentioned_time_text": ...,
        }
    """
    # If new time invalid, keep existing
    if new_start_ms is None or new_end_ms is None:
        if existing_state.has_mentioned_time:
            return {
                "mentioned_time_start_ms": existing_state.mentioned_time_start_ms,
                "mentioned_time_end_ms": existing_state.mentioned_time_end_ms,
                "mentioned_time_confidence": existing_state.mentioned_time_confidence,
                "mentioned_time_text": existing_state.mentioned_time_text,
            }
        return {}

    # If existing invalid, use new
    if not existing_state.has_mentioned_time:
        return {
            "mentioned_time_start_ms": new_start_ms,
            "mentioned_time_end_ms": new_end_ms,
            "mentioned_time_confidence": new_confidence,
            "mentioned_time_text": new_text,
        }

    # Both valid, take union
    merged_start = min(existing_state.mentioned_time_start_ms, new_start_ms)
    merged_end = max(existing_state.mentioned_time_end_ms, new_end_ms)

    # Validate merged time range
    if not validate_time_range(merged_start, merged_end):
        # If invalid, use existing time range (conservative strategy)
        logger.warning(
            f"Invalid merged time range for episode {existing_state.episode_id}: "
            f"start={merged_start}, end={merged_end}. Using existing time range."
        )
        merged_start = existing_state.mentioned_time_start_ms
        merged_end = existing_state.mentioned_time_end_ms

    # Weighted average confidence
    old_conf = existing_state.mentioned_time_confidence or 0.5
    new_conf = new_confidence or 0.5
    old_width = existing_state.mentioned_time_end_ms - existing_state.mentioned_time_start_ms
    new_width = new_end_ms - new_start_ms
    total_width = old_width + new_width
    if total_width > 0:
        merged_conf = (old_conf * old_width + new_conf * new_width) / total_width
    else:
        merged_conf = (old_conf + new_conf) / 2

    # Merge evidence text
    evidences = []
    if existing_state.mentioned_time_text:
        evidences.append(existing_state.mentioned_time_text)
    if new_text and new_text != existing_state.mentioned_time_text:
        evidences.append(new_text)
    merged_text = "; ".join(evidences)[:100] if evidences else None

    return {
        "mentioned_time_start_ms": merged_start,
        "mentioned_time_end_ms": merged_end,
        "mentioned_time_confidence": merged_conf,
        "mentioned_time_text": merged_text,
    }
