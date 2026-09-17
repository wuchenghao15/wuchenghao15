"""
Transform Edge context to graph visualization format.

Converts a list of Edge objects into nodes/edges structure
for graph rendering in the frontend.
"""

from __future__ import annotations

from typing import Any

from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge


def transform_context_to_graph(
    context: list[Edge],
) -> dict[str, list[dict[str, Any]]]:
    """
    Convert Edge list to graph visualization data.

    Args:
        context: List of Edge objects with node1, node2, and attributes.

    Returns:
        Dict with 'nodes' and 'edges' lists for graph rendering.
    """
    node_map: dict[str, dict] = {}
    edge_map: dict[str, dict] = {}

    for edge in context:
        n1 = edge.node1
        n2 = edge.node2
        attrs = edge.attributes

        # Extract source node
        n1_id = n1.id
        node_map[n1_id] = {
            "id": n1_id,
            "label": n1.attributes.get("name", n1_id),
            "type": n1.attributes.get("type"),
            "attributes": n1.attributes,
        }

        # Extract target node
        n2_id = n2.id
        node_map[n2_id] = {
            "id": n2_id,
            "label": n2.attributes.get("name", n2_id),
            "type": n2.attributes.get("type"),
            "attributes": n2.attributes,
        }

        # Create edge
        rel_name = attrs.get("relationship_name", "related")
        edge_key = f"{n1_id}_{rel_name}_{n2_id}"
        edge_map[edge_key] = {
            "source": n1_id,
            "target": n2_id,
            "label": rel_name,
        }

    return {
        "nodes": list(node_map.values()),
        "edges": list(edge_map.values()),
    }
