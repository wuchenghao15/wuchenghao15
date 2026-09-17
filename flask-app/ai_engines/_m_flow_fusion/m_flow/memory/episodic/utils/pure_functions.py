# m_flow/memory/episodic/utils/pure_functions.py
"""
Pure functions extracted from write_episodic_memories.py

This module contains pure functions (no side effects) that are used by
the episodic memory writing pipeline. All functions in this module are
synchronous and do not depend on external state.

Extracted as part of large file refactoring (Phase 1).

Functions:
    - _episode_sort_key: Sort FragmentDigest by (doc_id, chunk_index)
    - _extract_time_fields_from_episode: Extract time fields from episode dict
    - _split_long_summary: Split long summaries into chunks
    - _extract_chunk_summaries_from_text_summaries: Extract summaries from FragmentDigest
    - _create_facets_from_sections: Create Facets from FragmentDigest sections
    - _extract_all_sections_from_summaries: Extract all sections from summaries
    - _has_valid_sections: Check if any FragmentDigest has valid sections
    - _extract_event_sentences: Extract sentences for specific event_ids
    - _create_facets_from_sections_direct: Create Facets from Section list
    - _generate_episode_summary_from_sections: Generate Episode summary
    - _extract_entities_from_chunk: Extract entities from chunk.contains
    - ensure_nodeset: Ensure MemoryNode.memory_spaces contains nodeset
    - _choose_better_description: Choose better description by length
    - _create_same_entity_as_edges: Create same_entity_as edges
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from m_flow.knowledge.summarization.models import FragmentDigest

# Domain models
from m_flow.core import Edge
from m_flow.core.domain.models import Entity  # Entity is new, Entity is alias
from m_flow.core.domain.models.memory_space import MemorySpace

# Local module imports
from m_flow.memory.episodic.models import EpisodicFacetDraft

# External pure function dependencies
from m_flow.memory.episodic.edge_text_generators import make_same_entity_as_edge_text
from m_flow.memory.episodic.sentence_level_routing import (
    has_v2_routing,
    get_sentence_classifications,
    group_all_events,
)
from m_flow.memory.episodic.normalization import normalize_for_compare

# Logger
from m_flow.shared.logging_utils import get_logger

logger = get_logger("episodic.utils.pure_functions")

# ============================================================
# Constants
# ============================================================

# Patterns for splitting long summaries into multiple chunks
_SECTION_PATTERNS = [
    # Chinese numbered sections: 一、二、三、...
    r"(?=(?:^|\n)\s*[一二三四五六七八九十]+[、.．]\s*)",
    # Arabic numbered sections: 1. 2. 3. ...
    r"(?=(?:^|\n)\s*\d+[.、．]\s*)",
    # Markdown headers: # ## ###
    r"(?=(?:^|\n)\s*#{1,3}\s+)",
    # Bullet points: - * •
    r"(?=(?:^|\n)\s*[-*•]\s+)",
]


# ============================================================
# Pure Functions
# ============================================================


def _episode_sort_key(ts: "FragmentDigest") -> tuple:
    """
    Used to sort FragmentDigest by (doc_id, chunk_index)

    Step 3C: Extracted from inline function in write_episodic_memories to module-level function

    Args:
        ts: FragmentDigest object

    Returns:
        (doc_id, chunk_index) tuple for sorting
    """
    ch = ts.made_from
    d = getattr(ch, "is_part_of", None)
    did = str(getattr(d, "id", ""))
    return (did, int(getattr(ch, "chunk_index", 0)))


def _extract_time_fields_from_episode(episode_time_dict: dict) -> dict:
    """
    Extract time fields from merged_time dictionary for propagation to child nodes.

    Args:
        episode_time_dict: Dictionary returned by merge_episode_times()

    Returns:
        Dictionary suitable for direct expansion into MemoryNode constructor
    """
    return {
        "mentioned_time_start_ms": episode_time_dict.get("mentioned_time_start_ms"),
        "mentioned_time_end_ms": episode_time_dict.get("mentioned_time_end_ms"),
        "mentioned_time_confidence": episode_time_dict.get("mentioned_time_confidence"),
        "mentioned_time_text": episode_time_dict.get("mentioned_time_text"),
    }


def _split_long_summary(summaries: List[str], min_split_len: int = 200, max_items: int = 10) -> List[str]:
    """
    Split long summaries into multiple shorter items.

    When only 1 summary is provided and it's long, try to split it by
    document structure (sections, bullet points, etc.) to help LLM
    generate multiple facets.

    Args:
        summaries: List of summary strings
        min_split_len: Minimum length of summary to trigger splitting
        max_items: Maximum number of items to return

    Returns:
        List of summary strings (possibly more than input)
    """
    if not summaries:
        return summaries

    # Only split if there's exactly 1 summary and it's long
    if len(summaries) != 1 or len(summaries[0]) < min_split_len:
        return summaries

    text = summaries[0]

    # Try each pattern to split
    for pattern in _SECTION_PATTERNS:
        parts = re.split(pattern, text)
        # Clean and filter parts
        parts = [p.strip() for p in parts if p and p.strip()]
        # Only use this pattern if it produces 2+ meaningful parts
        if len(parts) >= 2 and all(len(p) >= 20 for p in parts):
            logger.info(f"[episodic] Split long summary into {len(parts)} parts using pattern: {pattern[:30]}...")
            return parts[:max_items]

    # If no pattern worked, try splitting by semicolon (Chinese or English)
    if "；" in text or ";" in text:
        # Replace English semicolon with Chinese
        normalized = text.replace(";", "；")
        parts = normalized.split("；")
        # Group small parts together (min 30 chars per group)
        grouped = []
        current_group = []
        current_len = 0
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if current_len + len(p) < 80:
                current_group.append(p)
                current_len += len(p)
            else:
                if current_group:
                    grouped.append("；".join(current_group))
                current_group = [p]
                current_len = len(p)
        if current_group:
            grouped.append("；".join(current_group))

        if len(grouped) >= 2:
            logger.info(f"[episodic] Split long summary into {len(grouped)} parts using semicolon")
            return grouped[:max_items]

    # No splitting possible, return as-is
    return summaries


def _extract_chunk_summaries_from_text_summaries(
    text_summaries: List["FragmentDigest"],
    max_items: int = 40,
    target_event_id: Optional[str] = None,
) -> List[str]:
    """
    Extract chunk summaries from FragmentDigest list, preferring sections if available.

    Priority order:
    1. V2 sentence-level routing: Use classified sentences grouped by event
       - If target_event_id is specified, only extract that event's content
       - Otherwise, extract all events (for Facet generation)
    2. Sectioned summarization: Each section becomes a chunk summary item
    3. Fallback: Use full text

    No truncation is applied to preserve complete information.

    Args:
        text_summaries: List of FragmentDigest objects
        max_items: Maximum number of items to return
        target_event_id: If specified, only extract content for this event_id (V2 mode).
                        Used in Episode Routing to ensure each event is routed independently.

    Returns:
        List of summary strings (one per section or per FragmentDigest)
    """

    result: List[str] = []

    for ts in text_summaries:
        chunk = ts.made_from

        # Priority 1: V2 sentence-level routing
        if has_v2_routing(chunk):
            all_sentences = get_sentence_classifications(chunk)

            if all_sentences:
                if target_event_id:
                    # Filter to ONLY the target event's sentences
                    # This ensures Episode Routing sees only the current event's content
                    event_sentences = [c for c in all_sentences if c.get("event_id") == target_event_id]

                    if event_sentences:
                        # Get topic from first sentence
                        topic = event_sentences[0].get("event_topic") or event_sentences[0].get("suggested_topic") or ""
                        sentences = [c.get("text", "").strip() for c in event_sentences if c.get("text", "").strip()]

                        if sentences:
                            event_text = " ".join(sentences)
                            if topic:
                                event_text = f"【{topic}】{event_text}"
                            result.append(event_text.strip())
                else:
                    # No target_event_id: extract ALL events (for Facet generation)
                    event_groups = group_all_events(all_sentences)

                    for _event_id, event_data in event_groups.items():  # noqa: PERF102
                        topic = event_data.get("topic", "")
                        sentences = event_data.get("sentences", [])

                        if sentences:
                            event_text = " ".join(sentences)
                            if topic:
                                event_text = f"【{topic}】{event_text}"
                            result.append(event_text.strip())

                continue  # Skip other methods for this FragmentDigest

        # Priority 2: Sectioned summarization
        sections = getattr(ts, "sections", None)

        if sections and len(sections) > 0:
            # Use section contents - each section becomes a chunk summary item
            for sec in sections:
                section_text = f"【{sec.heading}】{sec.text}"
                if section_text.strip():
                    result.append(section_text.strip())
        else:
            # Priority 3: Fallback to full text (no truncation)
            text = getattr(ts, "text", "") or ""
            if text.strip():
                result.append(text.strip())

    # Apply limit
    if len(result) > max_items:
        logger.info(f"[episodic] Limiting chunk_summaries from {len(result)} to {max_items} items")
        result = result[:max_items]

    return result


def _create_facets_from_sections(
    text_summaries: List["FragmentDigest"],
) -> List["EpisodicFacetDraft"]:
    """
    Directly create Facets from FragmentDigest sections (no LLM call).

    When sectioned summarization is enabled:
    - section.title → Facet.search_text (15-50 chars, retrieval anchor)
    - section.content → Facet.description (full facts, used as facet_anchor_text)

    This bypasses the Facet generation LLM, ensuring zero information loss
    since the section content is directly used as the Facet description.

    Args:
        text_summaries: List of FragmentDigest with populated sections

    Returns:
        List of EpisodicFacetDraft objects
    """

    facets: List[EpisodicFacetDraft] = []
    seen_titles: set = set()

    for ts in text_summaries:
        sections = getattr(ts, "sections", None)
        if not sections:
            continue

        for sec in sections:
            title = (sec.heading or "").strip()
            content = (sec.text or "").strip()

            if not title or not content:
                continue

            # Normalize title for deduplication
            title_norm = normalize_for_compare(title)
            if title_norm in seen_titles:
                continue
            seen_titles.add(title_norm)

            # Create Facet directly from section
            facet = EpisodicFacetDraft(
                facet_type="topic",  # Generic type for section-based facets
                search_text=title,  # section.title as search anchor
                description=content,  # section.content as full description
                aliases=[],  # No aliases from sections
            )
            facets.append(facet)

    logger.info(f"[episodic] Created {len(facets)} facets directly from sections (no LLM)")
    return facets


def _extract_all_sections_from_summaries(
    text_summaries: List["FragmentDigest"],
) -> List[tuple]:
    """
    Extract all sections from FragmentDigest list.

    Returns:
        List of (title, content) tuples
    """
    sections = []
    for ts in text_summaries:
        ts_sections = getattr(ts, "sections", None)
        if ts_sections:
            for sec in ts_sections:
                title = (sec.heading or "").strip()
                content = (sec.text or "").strip()
                if title and content:
                    sections.append((title, content))
    return sections


def _has_valid_sections(text_summaries: List["FragmentDigest"]) -> bool:
    """Check if any FragmentDigest has valid sections."""
    for ts in text_summaries:
        sections = getattr(ts, "sections", None)
        if sections and len(sections) > 0:
            for sec in sections:
                if (sec.heading or "").strip() and (sec.text or "").strip():
                    return True
    return False


def _extract_event_sentences(
    doc_summaries: List["FragmentDigest"],
    source_event_ids: List[str],
    original_event_routing_types: Dict[str, str],
) -> Tuple[List[str], str, bool]:
    """
    Extract sentences belonging to specified event_ids from FragmentDigest's made_from chunk

    Args:
        doc_summaries: List of FragmentDigest associated with Episode
        source_event_ids: Original event_ids for this Episode (from episode_source_events)
        original_event_routing_types: event_id -> routing_type mapping

    Returns:
        Tuple of (sentences, topic, is_atomic)
    """
    sentences = []
    topic = ""
    is_atomic = True  # Default atomic, becomes False if any episodic exists

    source_event_ids_set = set(source_event_ids)

    for ts in doc_summaries:
        chunk = ts.made_from
        classifications = chunk.metadata.get("sentence_classifications", [])

        for c in classifications:
            event_id = c.get("event_id")
            if event_id and event_id in source_event_ids_set:
                text = c.get("text", "").strip()
                if text:
                    sentences.append(text)

                # Get topic (take first non-empty)
                if not topic:
                    topic = c.get("event_topic", "") or c.get("suggested_topic", "")

                # Determine if atomic
                routing_type = original_event_routing_types.get(event_id) or c.get("routing_type", "episodic")
                if routing_type == "episodic":
                    is_atomic = False

    # Fallback: when Content Routing is disabled, chunks have no
    # sentence_classifications.  Use full chunk text instead so that
    # summarize_by_event can still generate proper sections/facets.
    if not sentences:
        is_atomic = False  # multi-section by default
        for ts in doc_summaries:
            chunk_text = (ts.made_from.text if ts.made_from else "").strip()
            if chunk_text:
                sentences.append(chunk_text)
            if not topic:
                topic = getattr(ts, "overall_topic", None) or "Content"

    return sentences, topic, is_atomic


def _create_facets_from_sections_direct(
    sections: List,  # List[Section]
) -> List["EpisodicFacetDraft"]:
    """
    Directly create Facets from Section list (not via FragmentDigest)

    Used for Event-Level Sections functionality, creating Facets from summarize_by_event output.

    Args:
        sections: List of Section objects

    Returns:
        List of EpisodicFacetDraft
    """

    facets = []
    seen_titles = set()

    for sec in sections:
        title = (sec.heading or "").strip()
        content = (sec.text or "").strip()

        if not title or not content:
            continue

        title_norm = normalize_for_compare(title)
        if title_norm in seen_titles:
            continue
        seen_titles.add(title_norm)

        facets.append(
            EpisodicFacetDraft(
                facet_type="topic",
                search_text=title,
                description=content,
                aliases=[],
            )
        )

    return facets


def _generate_episode_summary_from_sections(sections: List) -> str:
    """
    Generate Episode.summary from sections

    Args:
        sections: List of Section objects

    Returns:
        Formatted summary string
    """
    if not sections:
        return "Episode content"

    section_contents = []
    for sec in sections:
        title = (sec.heading or "").strip()
        content = (sec.text or "").strip()
        if title and content:
            section_contents.append(f"【{title}】{content}")

    if section_contents:
        return " ".join(section_contents)

    return "Episode content"


def _extract_entities_from_chunk(chunk) -> Tuple[List[Entity], Dict[str, int]]:
    """Extract Entity list and frequency statistics from ContentFragment.contains"""
    entities: List[Entity] = []
    freq: Dict[str, int] = {}

    contains = getattr(chunk, "contains", None) or []
    for item in contains:
        ent = None
        if isinstance(item, Entity):
            ent = item
        elif isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], Entity):
            ent = item[1]
        if ent is None:
            continue

        entities.append(ent)
        freq[ent.name] = freq.get(ent.name, 0) + 1

    # Deduplicate (by id)
    seen = set()
    uniq: List[Entity] = []
    for e in entities:
        eid = str(e.id)
        if eid in seen:
            continue
        seen.add(eid)
        uniq.append(e)

    return uniq, freq


def ensure_nodeset(dp, nodeset: MemorySpace) -> None:
    """Ensure MemoryNode.memory_spaces contains nodeset"""
    if getattr(dp, "memory_spaces", None) is None:
        dp.memory_spaces = [nodeset]
        return
    if not any(str(ns.id) == str(nodeset.id) for ns in dp.memory_spaces):
        dp.memory_spaces.append(nodeset)


def _choose_better_description(old: Optional[str], new: Optional[str]) -> Optional[str]:
    """
    Choose better description by comparing lengths.

    Args:
        old: Old description string
        new: New description string

    Returns:
        The longer description, or None if both are empty
    """
    old = (old or "").strip()
    new = (new or "").strip()
    if not old and not new:
        return None
    if len(new) > len(old):
        return new
    return old


def _create_same_entity_as_edges(
    new_entity: Entity,
    existing_entities: List[Dict[str, Any]],
) -> List[Tuple[Edge, Entity]]:
    """
    Create same_entity_as edges linking a new entity to existing same-name entities.

    Args:
        new_entity: The newly created Entity
        existing_entities: List of existing entities with same canonical_name

    Returns:
        List of (Edge, target_Concept) tuples for the same_entity_as relationship
    """
    edges = []

    for existing in existing_entities:
        # Create a proxy Entity for the existing entity (just for edge creation)
        # The actual entity already exists in the graph
        proxy_entity = Entity(
            id=existing["id"],
            name=existing["name"],
            description=existing.get("description", ""),
            canonical_name=existing.get("canonical_name", ""),
            memory_type=existing.get("memory_type"),  # Inherit from existing entity
        )

        edge = Edge(
            relationship_type="same_entity_as",
            edge_text=make_same_entity_as_edge_text(new_entity, proxy_entity),
        )
        edges.append((edge, proxy_entity))

    return edges


# ============================================================
# Module exports
# ============================================================

__all__ = [
    # Constants
    "_SECTION_PATTERNS",
    # Pure functions
    "_episode_sort_key",
    "_extract_time_fields_from_episode",
    "_split_long_summary",
    "_extract_chunk_summaries_from_text_summaries",
    "_create_facets_from_sections",
    "_extract_all_sections_from_summaries",
    "_has_valid_sections",
    "_extract_event_sentences",
    "_create_facets_from_sections_direct",
    "_generate_episode_summary_from_sections",
    "_extract_entities_from_chunk",
    "ensure_nodeset",
    "_choose_better_description",
    "_create_same_entity_as_edges",
]
