# m_flow/memory/episodic/edge_text_generators.py
"""
Edge text generation module.

Generate rich text descriptions for various relationship edges, used for:
- Vector search indexing
- Debugging and visualization
- Retrieval path optimization

Optimization notes:
- Remove structured prefixes (e.g., "relationship_name: has_facet;")
- Mimic Procedural's concise format to reduce semantic interference during vector search
- Format: "Title: Description" or "Title | Description"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .normalization import truncate

if TYPE_CHECKING:
    pass  # Entity is the new name for Entity


def make_has_facet_edge_text(facet_type: str, facet_search_text: str, facet_description: str = "") -> str:
    """
    Generate edge_text for has_facet edge.

    Concise format to reduce structured prefix interference with vector search.

    Args:
        facet_type: Facet type
        facet_search_text: Facet search text
        facet_description: Facet description

    Returns:
        Formatted edge text (concise format)
    """
    desc = truncate(facet_description or "", 300)
    # Concise format: mimic Procedural
    if desc:
        return f"{facet_search_text}: {desc}"
    return facet_search_text


def make_involves_entity_edge_text(entity: "Entity", context_description: str = "") -> str:
    """
    Generate edge_text for involves_entity edge.

    Concise format: entity_name | description

    Args:
        entity: Entity object
        context_description: Episode-specific context description

    Returns:
        Formatted edge text (concise format)
    """
    desc = context_description or getattr(entity, "description", "") or ""
    desc = truncate(desc, 200)
    # Concise format
    if desc:
        return f"{entity.name} | {desc}"
    return entity.name


def make_same_entity_as_edge_text(entity_a: "Entity", entity_b: "Entity") -> str:
    """
    Generate edge_text for same_entity_as edge.

    Concise format: entityA = entityB (canonical_name)

    Args:
        entity_a: Source entity
        entity_b: Target entity

    Returns:
        Formatted edge text (concise format)
    """
    canonical = getattr(entity_a, "canonical_name", "") or entity_a.name.lower()
    # Concise format
    return f"{entity_a.name} = {entity_b.name} ({canonical})"


def make_supported_by_edge_text(facet_search_text: str, chunk_id: str, chunk_index: int, chunk_summary: str) -> str:
    """
    Generate edge_text for supported_by edge.

    Concise format: facet_title <- chunk_summary

    Args:
        facet_search_text: Facet search text
        chunk_id: Chunk ID
        chunk_index: Chunk index
        chunk_summary: Chunk summary

    Returns:
        Formatted edge text (concise format)
    """
    summary = (chunk_summary or "").strip()
    if len(summary) > 160:
        summary = summary[:159] + "…"
    # Concise format
    if summary:
        return f"{facet_search_text} <- {summary}"
    return f"{facet_search_text} <- chunk#{chunk_index}"


def make_includes_chunk_edge_text(chunk_id: str, chunk_index: int) -> str:
    """
    Generate edge_text for includes_chunk edge.

    Concise format: chunk#index

    Args:
        chunk_id: Chunk ID
        chunk_index: Chunk index

    Returns:
        Formatted edge text (concise format)
    """
    # Concise format (this edge mainly for relationship tracking, not search focus)
    return f"chunk#{chunk_index}"


def make_has_point_edge_text(
    facet_type: str,
    facet_search_text: str,
    point_search_text: str,
    point_description: str = "",
) -> str:
    """
    Generate edge_text for has_point edge.

    Concise format: facet_title -> point_title: point_description

    Args:
        facet_type: Facet type
        facet_search_text: Facet search text
        point_search_text: FacetPoint search text
        point_description: FacetPoint description

    Returns:
        Formatted edge text (concise format)
    """
    desc = truncate(point_description, 200)
    # Concise format
    if desc:
        return f"{facet_search_text} -> {point_search_text}: {desc}"
    return f"{facet_search_text} -> {point_search_text}"


def make_facet_involves_entity_edge_text(
    entity_name: str,
    entity_description: str = "",
    facet_search_text: str = "",
) -> str:
    """
    Generate edge_text for Facet -> Entity (involves_entity) edge.

    This edge connects a Facet to an Entity that appears in that Facet's content.
    The format is similar to Episode -> Entity edge but includes facet context.

    Concise format: entity_name | description (in facet_context)

    Args:
        entity_name: Entity name (must be exact original text from content)
        entity_description: Entity description
        facet_search_text: Optional facet search text for context

    Returns:
        Formatted edge text (concise format)
    """
    desc = truncate(entity_description, 180)
    # Include facet context if available, otherwise same as Episode-Entity edge
    if desc and facet_search_text:
        return f"{entity_name} | {desc} (in: {truncate(facet_search_text, 50)})"
    elif desc:
        return f"{entity_name} | {desc}"
    elif facet_search_text:
        return f"{entity_name} (in: {truncate(facet_search_text, 50)})"
    return entity_name


# ============================================================
# Backward compatibility aliases (with underscore prefix)
# ============================================================

_make_has_facet_edge_text = make_has_facet_edge_text
_make_involves_entity_edge_text = make_involves_entity_edge_text
_make_same_entity_as_edge_text = make_same_entity_as_edge_text
_make_supported_by_edge_text = make_supported_by_edge_text
_make_includes_chunk_edge_text = make_includes_chunk_edge_text
_make_has_point_edge_text = make_has_point_edge_text
_make_facet_involves_entity_edge_text = make_facet_involves_entity_edge_text
