# m_flow/memory/episodic/context_vars.py
"""
Thread/coroutine-safe context variable management module

Uses contextvars to provide coroutine-safe global state management:
- Pending queue for same_entity_as edges

Step 3D: Extracted from write_episodic_memories.py
Note: Step 1 has already changed global variables to ContextVar
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Dict, List, Optional


# ============================================================
# Pending queue for same_entity_as edges
# ============================================================

_pending_same_entity_edges_ctx: ContextVar[Optional[List[Dict[str, str]]]] = ContextVar(
    "pending_same_entity_edges", default=None
)


def get_pending_same_entity_edges() -> List[Dict[str, str]]:
    """
    Get the same_entity_as edge list for the current context

    If the current context is not initialized, automatically creates an empty list.

    Returns:
        List of edge data
    """
    val = _pending_same_entity_edges_ctx.get()
    if val is None:
        val = []
        _pending_same_entity_edges_ctx.set(val)
    return val


def add_pending_same_entity_edge(edge_data: Dict[str, str]) -> None:
    """
    Add same_entity_as edge to pending queue

    Args:
        edge_data: Edge data dictionary, containing source_id, target_id, relationship_name, edge_text
    """
    get_pending_same_entity_edges().append(edge_data)


def get_and_clear_pending_same_entity_edges() -> List[Dict[str, str]]:
    """
    Get and clear the same_entity_as edge list

    Returns:
        All pending edge data
    """
    edges = get_pending_same_entity_edges().copy()
    _pending_same_entity_edges_ctx.set([])
    return edges


# ============================================================
# Pending queue for Facet-Entity edges
# ============================================================

_pending_facet_entity_edges_ctx: ContextVar[Optional[List[Dict[str, str]]]] = ContextVar(
    "pending_facet_entity_edges", default=None
)


def get_pending_facet_entity_edges() -> List[Dict[str, str]]:
    """
    Get the Facet-Entity edge list for the current context

    If the current context is not initialized, automatically creates an empty list.

    Returns:
        List of edge data
    """
    val = _pending_facet_entity_edges_ctx.get()
    if val is None:
        val = []
        _pending_facet_entity_edges_ctx.set(val)
    return val


def add_pending_facet_entity_edge(edge_data: Dict[str, str]) -> None:
    """
    Add Facet-Entity edge to pending queue

    Args:
        edge_data: Edge data dictionary, containing source_id, target_id, relationship_name, edge_text
    """
    get_pending_facet_entity_edges().append(edge_data)


def get_and_clear_pending_facet_entity_edges() -> List[Dict[str, str]]:
    """
    Get and clear the Facet-Entity edge list

    Returns:
        All pending edge data
    """
    edges = get_pending_facet_entity_edges().copy()
    _pending_facet_entity_edges_ctx.set([])
    return edges


# ============================================================
# Convenience aliases
# ============================================================

# These aliases are used to maintain the original naming style in write_episodic_memories.py
_get_pending_same_entity_edges = get_pending_same_entity_edges
_add_pending_same_entity_edge = add_pending_same_entity_edge
_get_and_clear_pending_same_entity_edges = get_and_clear_pending_same_entity_edges

_get_pending_facet_entity_edges = get_pending_facet_entity_edges
_add_pending_facet_entity_edge = add_pending_facet_entity_edge
_get_and_clear_pending_facet_entity_edges = get_and_clear_pending_facet_entity_edges
