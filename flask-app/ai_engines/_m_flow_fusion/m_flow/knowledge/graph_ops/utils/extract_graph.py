"""
Graph Extraction from Memory Models

Traverses MemoryNode structures to extract nodes and edges
for storage in graph databases. Handles nested relationships,
edge metadata, and cycle detection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from m_flow.core import Edge, MemoryNode

# Type aliases
NodeId = str
EdgeTuple = tuple[Any, Any, str, dict[str, Any]]
EdgeWithNodes = tuple["Edge | None", list["MemoryNode"]]


# ---------------------------------------------------------------------------
# Field Analysis
# ---------------------------------------------------------------------------


def _is_memory_node(obj: Any) -> bool:
    """Check if object is a MemoryNode instance."""
    from m_flow.core import MemoryNode

    return isinstance(obj, MemoryNode)


def _is_edge_instance(obj: Any) -> bool:
    """Check if object is an Edge instance."""
    from m_flow.core import Edge

    return isinstance(obj, Edge)


def _parse_field_content(value: Any) -> list[EdgeWithNodes]:
    """
    Analyze a field value and extract any edge-node pairs.

    Returns list of (edge_metadata, nodes) tuples. Empty list means
    the field is a regular property, not a relationship.
    """
    # Direct MemoryNode
    if _is_memory_node(value):
        return [(None, [value])]

    # Tuple format: (Edge, MemoryNode) or (Edge, [MemoryNode, ...])
    if isinstance(value, tuple) and len(value) == 2:
        edge_candidate, data_candidate = value
        if _is_edge_instance(edge_candidate):
            if _is_memory_node(data_candidate):
                return [(edge_candidate, [data_candidate])]
            if isinstance(data_candidate, list) and data_candidate and _is_memory_node(data_candidate[0]):
                return [(edge_candidate, data_candidate)]

    # List format: may contain nodes, tuples, or mixed
    if isinstance(value, list) and value:
        extracted = []
        for item in value:
            # Tuple in list
            if isinstance(item, tuple) and len(item) == 2:
                edge_obj, data_obj = item
                if _is_edge_instance(edge_obj):
                    if _is_memory_node(data_obj):
                        extracted.append((edge_obj, [data_obj]))
                    elif isinstance(data_obj, list) and data_obj and _is_memory_node(data_obj[0]):
                        extracted.append((edge_obj, data_obj))
            # Direct node in list
            elif _is_memory_node(item):
                extracted.append((None, [item]))
        return extracted

    return []


# ---------------------------------------------------------------------------
# Edge Property Construction
# ---------------------------------------------------------------------------


def _build_edge_attributes(
    src: str,
    dst: str,
    rel_name: str,
    meta: "Edge | None",
) -> dict[str, Any]:
    """
    Construct edge property dictionary.

    Includes standard fields plus any custom metadata from the Edge object.
    Weights are flattened for easier querying.
    """
    attrs = {
        "source_node_id": src,
        "target_node_id": dst,
        "relationship_name": rel_name,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    if meta is None:
        return attrs

    # Merge edge metadata
    meta_dict = meta.model_dump(exclude_none=True)
    attrs.update(meta_dict)

    # Flatten weights for easier graph queries
    if meta.weights:
        for weight_key, weight_val in meta.weights.items():
            attrs[f"weight_{weight_key}"] = weight_val

    return attrs


def _determine_relationship_label(field: str, meta: "Edge | None") -> str:
    """Get relationship type from edge metadata or default to field name."""
    if meta and getattr(meta, "relationship_type", None):
        return meta.relationship_type
    return field


def _make_visit_key(node_id: str, rel: str, target_id: str) -> str:
    """Generate unique key for tracking visited relationships."""
    return f"{node_id}_{rel}_{target_id}"


# ---------------------------------------------------------------------------
# Relationship Iteration
# ---------------------------------------------------------------------------


def _iter_relationships(
    node: "MemoryNode",
    fields_to_process: set[str],
) -> Generator[tuple["MemoryNode", str, "Edge | None"], None, None]:
    """
    Yield all relationship targets from specified fields.

    Generates: (target_node, field_name, edge_metadata)
    """
    for fname in fields_to_process:
        fval = getattr(node, fname)
        pairs = _parse_field_content(fval)

        for edge_meta, targets in pairs:
            for target in targets:
                yield target, fname, edge_meta


# ---------------------------------------------------------------------------
# Main Extraction Function
# ---------------------------------------------------------------------------


async def extract_graph(
    memory_node: "MemoryNode",
    added_nodes: dict[str, bool],
    added_edges: dict[str, bool],
    visited_properties: dict[str, bool] | None = None,
    include_root: bool = True,
) -> tuple[list["MemoryNode"], list[EdgeTuple]]:
    """
    Recursively extract graph structure from a MemoryNode.

    Traverses the node's relationships, building a list of nodes
    and edges suitable for graph database storage. Handles cycles
    via visited tracking.

    Args:
        memory_node: Root node to extract from.
        added_nodes: Tracks processed node IDs (mutated in place).
        added_edges: Tracks processed edge keys (mutated in place).
        visited_properties: Tracks visited relationships (cycle prevention).
        include_root: Whether to include the root node in output.

    Returns:
        Tuple of (nodes_list, edges_list).
    """
    from m_flow.storage.utils_mod.utils import copy_model

    node_id = str(memory_node.id)

    # Already processed this node
    if node_id in added_nodes:
        return [], []

    visited_properties = visited_properties or {}
    collected_nodes: list["MemoryNode"] = []
    collected_edges: list[EdgeTuple] = []

    # Categorize fields
    node_props = {"type": type(memory_node).__name__}
    relationship_fields: set[str] = set()
    excluded_attrs: set[str] = set()

    for attr_name, attr_val in memory_node:
        parsed = _parse_field_content(attr_val)

        if not parsed:
            # Regular property
            node_props[attr_name] = attr_val
        else:
            # Relationship field
            excluded_attrs.add(attr_name)
            for edge_meta, targets in parsed:
                rel_label = _determine_relationship_label(attr_name, edge_meta)
                for t in targets:
                    vkey = _make_visit_key(node_id, rel_label, str(t.id))
                    if vkey not in visited_properties:
                        relationship_fields.add(attr_name)

    # Add root node if requested
    if include_root and node_id not in added_nodes:
        SlimModel = copy_model(type(memory_node), exclude_fields=list(excluded_attrs))
        collected_nodes.append(SlimModel(**node_props))
        added_nodes[node_id] = True

    # Process relationships
    for target, fname, edge_meta in _iter_relationships(memory_node, relationship_fields):
        rel_label = _determine_relationship_label(fname, edge_meta)

        # Create edge
        edge_key = f"{node_id}_{target.id}_{fname}"
        if edge_key not in added_edges:
            attrs = _build_edge_attributes(memory_node.id, target.id, rel_label, edge_meta)
            collected_edges.append((memory_node.id, target.id, rel_label, attrs))
            added_edges[edge_key] = True

        # Mark as visited
        vkey = _make_visit_key(node_id, rel_label, str(target.id))
        visited_properties[vkey] = True

        # Recurse into unprocessed targets
        if str(target.id) not in added_nodes:
            child_nodes, child_edges = await extract_graph(
                target,
                added_nodes=added_nodes,
                added_edges=added_edges,
                visited_properties=visited_properties,
                include_root=True,
            )
            collected_nodes.extend(child_nodes)
            collected_edges.extend(child_edges)

    return collected_nodes, collected_edges


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------


def get_own_property_nodes(
    nodes: list["MemoryNode"],
    edges: list[EdgeTuple],
) -> list["MemoryNode"]:
    """
    Return nodes that are not edge destinations.

    Filters out any node whose ID appears as a target in the edge list.
    Useful for finding "root" or "orphan" nodes.
    """
    target_ids = {str(e[1]) for e in edges}
    return [n for n in nodes if str(n.id) not in target_ids]
