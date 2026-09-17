"""
Graph to model reconstruction.

Rebuilds Pydantic models from graph nodes and edges.
"""

from __future__ import annotations

from pydantic_core import PydanticUndefined

from m_flow.core import MemoryNode
from m_flow.storage.utils_mod.utils import copy_model


def get_model_instance_from_graph(
    nodes: list[MemoryNode],
    edges: list,
    entity_id: str,
) -> MemoryNode:
    """
    Reconstruct model with relationships from graph.

    Processes edges to build nested model structure.

    Args:
        nodes: Graph nodes.
        edges: Edge tuples (source, target, label, [props]).
        entity_id: Root entity to reconstruct.

    Returns:
        Model instance with populated relationships.
    """
    # Build lookup map
    lookup = {node.id: node for node in nodes}

    # Process edges to build relationships
    for edge in edges:
        source_id = edge[0]
        target_id = edge[1]
        label = edge[2]
        props = edge[3] if len(edge) >= 4 else {}

        source = lookup[source_id]
        target = lookup[target_id]

        # Determine relationship type
        meta = props.get("metadata", {})
        is_list = meta.get("type") == "list"

        # Create new model with relationship field
        target_type = type(target)
        field_type = list[target_type] if is_list else target_type
        field_value = [target] if is_list else target

        extended = copy_model(
            type(source),
            {label: (field_type, PydanticUndefined)},
        )

        lookup[source_id] = extended(
            **source.model_dump(),
            **{label: field_value},
        )

    return lookup[entity_id]
