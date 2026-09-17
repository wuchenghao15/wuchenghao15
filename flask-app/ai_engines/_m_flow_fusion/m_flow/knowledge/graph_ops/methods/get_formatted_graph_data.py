"""
Graph data formatting for visualization.

Transforms raw graph data into frontend-compatible format.
"""

from __future__ import annotations

from uuid import UUID

from m_flow.adapters.graph import get_graph_provider
from m_flow.auth.models import User
from m_flow.context_global_variables import set_db_context
from m_flow.data.exceptions.exceptions import DatasetNotFoundError
from m_flow.data.methods import get_authorized_dataset


async def get_formatted_graph_data(dataset_id: UUID, user: User) -> dict:
    """
    Retrieve graph data formatted for UI.

    Args:
        dataset_id: Target dataset.
        user: Requesting user.

    Returns:
        Dict with nodes and edges lists.

    Raises:
        DatasetNotFoundError: Dataset not found or unauthorized.
    """
    dataset = await get_authorized_dataset(user, dataset_id)
    if not dataset:
        raise DatasetNotFoundError(message="Dataset not found")

    await set_db_context(dataset_id, dataset.owner_id)

    engine = await get_graph_provider()
    nodes, edges = await engine.get_graph_data()

    return {
        "nodes": [_format_node(n) for n in nodes],
        "edges": [_format_edge(e) for e in edges],
    }


def _format_node(node: tuple) -> dict:
    """Convert node tuple to dict."""
    node_id, props = node

    # Determine display label
    name = props.get("name", "")
    node_type = props.get("type", "Unknown")
    label = name if name else f"{node_type}_{node_id}"

    # Filter properties
    skip_keys = {"id", "type", "name", "created_at", "updated_at"}
    filtered = {k: v for k, v in props.items() if k not in skip_keys and v is not None}

    return {
        "id": str(node_id),
        "label": label,
        "type": node_type,
        "properties": filtered,
    }


def _format_edge(edge: tuple) -> dict:
    """Convert edge tuple to dict."""
    return {
        "source": str(edge[0]),
        "target": str(edge[1]),
        "relationship": str(edge[2]),
    }
