"""Node and edge deduplication utility."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from m_flow.core import MemoryNode


def deduplicate_nodes_and_edges(
    nodes: List[MemoryNode],
    edges: List[Any],
) -> Tuple[List[MemoryNode], List[Any]]:
    """Remove duplicate nodes and edges based on their IDs."""
    seen_nodes: Dict[str, bool] = {}
    seen_edges: Dict[str, bool] = {}
    unique_nodes: List[MemoryNode] = []
    unique_edges: List[Any] = []

    for node in nodes:
        key = str(node.id)
        if key not in seen_nodes:
            unique_nodes.append(node)
            seen_nodes[key] = True

    for edge in edges:
        key = f"{edge[0]}|{edge[2]}|{edge[1]}"
        if key not in seen_edges:
            unique_edges.append(edge)
            seen_edges[key] = True

    return unique_nodes, unique_edges
