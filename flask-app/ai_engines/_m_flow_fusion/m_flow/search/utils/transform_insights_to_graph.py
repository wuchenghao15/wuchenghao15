"""
Transform triplet insights to graph visualization format.

Converts triplet data (subject, predicate, object) into nodes/edges
structure suitable for graph rendering.
"""

from __future__ import annotations

from typing import Any


def transform_insights_to_graph(
    context: list[tuple[dict, dict, dict]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Convert triplets to graph visualization data.

    Args:
        context: List of (subject, predicate, object) triplets.
                 Each element is a dict with 'id', 'name', 'type' keys.

    Returns:
        Dict with 'nodes' and 'edges' lists for graph rendering.
    """
    node_map: dict[str, dict] = {}
    edge_map: dict[str, dict] = {}

    for subj, pred, obj in context:
        # Extract node for subject
        subj_id = subj["id"]
        node_map[subj_id] = {
            "id": subj_id,
            "label": subj.get("name", subj_id),
            "type": subj["type"],
        }

        # Extract node for object
        obj_id = obj["id"]
        node_map[obj_id] = {
            "id": obj_id,
            "label": obj.get("name", obj_id),
            "type": obj["type"],
        }

        # Create edge from subject to object
        rel_name = pred["relationship_name"]
        edge_key = f"{subj_id}_{rel_name}_{obj_id}"
        edge_map[edge_key] = {
            "source": subj_id,
            "target": obj_id,
            "label": rel_name,
        }

    return {
        "nodes": list(node_map.values()),
        "edges": list(edge_map.values()),
    }
