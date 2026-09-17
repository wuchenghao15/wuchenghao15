"""
Edge Writers Module.

This module handles post-processing tasks for writing edges after persist_memory_nodes.
Extracted from write_episodic_memories.py during Phase 4 of the large file refactoring.

Main functions:
- write_same_entity_edges: Write same_entity_as edges between Entity nodes
- write_facet_entity_edges: Write involves_entity edges from Facets to Entities
"""

from __future__ import annotations

from typing import Any, List

from m_flow.shared.logging_utils import get_logger
from m_flow.adapters.graph import get_graph_provider
from m_flow.memory.episodic.context_vars import (
    _get_and_clear_pending_same_entity_edges,
    _get_and_clear_pending_facet_entity_edges,
)

logger = get_logger("episodic.edge_writers")


async def write_same_entity_edges(memory_nodes: List[Any]) -> List[Any]:
    """
    Post-processing task to write same_entity_as edges after persist_memory_nodes.

    This task should be run after persist_memory_nodes to ensure all Entity nodes
    exist in the graph before creating edges between them.

    Args:
        memory_nodes: The data points returned from persist_memory_nodes (passed through)

    Returns:
        The same memory_nodes (unchanged)
    """
    pending_edges = _get_and_clear_pending_same_entity_edges()

    if not pending_edges:
        logger.debug("[episodic] No pending same_entity_as edges to write")
        return memory_nodes

    try:
        graph_engine = await get_graph_provider()

        edges_to_add = [
            (
                e["source_id"],
                e["target_id"],
                e["relationship_name"],
                {
                    "relationship_name": e["relationship_name"],
                    "edge_text": e["edge_text"],
                },
            )
            for e in pending_edges
        ]

        await graph_engine.add_edges(edges_to_add)
        logger.info(
            f"[episodic] Wrote {len(edges_to_add)} same_entity_as edges "
            f"linking entities to their counterparts in other episodes"
        )
    except Exception as e:
        logger.warning(f"[episodic] Failed to write same_entity_as edges: {e}")

    return memory_nodes


async def write_facet_entity_edges(memory_nodes: List[Any]) -> List[Any]:
    """
    Post-processing task to write Facet-Entity edges after persist_memory_nodes.

    This task creates involves_entity edges from Facets to Entities,
    enabling fine-grained retrieval and precise Episode splitting.

    Design rationale:
    - Entity names are extracted with EXACT original form preservation
    - This allows efficient regex-based matching without semantic analysis
    - Edges are queued during write_episodic_memories and written here

    Args:
        memory_nodes: The data points returned from persist_memory_nodes (passed through)

    Returns:
        The same memory_nodes (unchanged)
    """
    pending_edges = _get_and_clear_pending_facet_entity_edges()

    if not pending_edges:
        logger.debug("[episodic] No pending Facet-Entity edges to write")
        return memory_nodes

    try:
        graph_engine = await get_graph_provider()

        edges_to_add = [
            (
                e["source_id"],
                e["target_id"],
                e["relationship_name"],
                {
                    "relationship_name": e["relationship_name"],
                    "edge_text": e["edge_text"],
                },
            )
            for e in pending_edges
        ]

        await graph_engine.add_edges(edges_to_add)
        logger.info(
            f"[episodic] Wrote {len(edges_to_add)} Facet-Entity edges linking facets to entities that appear in them"
        )
    except Exception as e:
        logger.warning(f"[episodic] Failed to write Facet-Entity edges: {e}")

    return memory_nodes


__all__ = ["write_same_entity_edges", "write_facet_entity_edges"]
