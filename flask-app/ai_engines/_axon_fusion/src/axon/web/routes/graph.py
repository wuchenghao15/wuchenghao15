"""Graph API routes — full graph, node detail, overview stats."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from axon.core.graph.model import GraphNode, GraphRelationship

logger = logging.getLogger(__name__)

router = APIRouter(tags=["graph"])


def _serialize_node(node: GraphNode) -> dict:
    """Convert a GraphNode to a camelCase dict for the frontend."""
    return {
        "id": node.id,
        "label": node.label.value,
        "name": node.name,
        "filePath": node.file_path,
        "startLine": node.start_line,
        "endLine": node.end_line,
        "signature": node.signature,
        "language": node.language,
        "className": node.class_name,
        "isDead": node.is_dead,
        "isEntryPoint": node.is_entry_point,
        "isExported": node.is_exported,
    }


def _serialize_edge(rel: GraphRelationship) -> dict:
    """Convert a GraphRelationship to a camelCase dict for the frontend."""
    return {
        "id": rel.id,
        "type": rel.type.value,
        "source": rel.source,
        "target": rel.target,
        "confidence": rel.properties.get("confidence", 1.0),
        "strength": rel.properties.get("strength"),
        "stepNumber": rel.properties.get("step_number"),
    }


@router.get("/graph")
def get_graph(request: Request) -> dict:
    """Load the full knowledge graph and serialize all nodes and edges."""
    storage = request.app.state.storage
    try:
        graph = storage.load_graph()
    except Exception as exc:
        logger.error("Failed to load graph: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load graph") from exc

    nodes = [_serialize_node(n) for n in graph.iter_nodes()]
    edges = [_serialize_edge(r) for r in graph.iter_relationships()]

    return {"nodes": nodes, "edges": edges, "total": len(nodes)}


@router.get("/node/{node_id:path}")
def get_node(node_id: str, request: Request) -> dict:
    """Get a single node with its callers, callees, type refs, and process memberships."""
    if len(node_id) > 500:
        raise HTTPException(status_code=400, detail="Node ID too long")

    storage = request.app.state.storage

    node = storage.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    callers = [
        {"node": _serialize_node(n), "confidence": conf}
        for n, conf in storage.get_callers_with_confidence(node_id)
    ]

    callees = [
        {"node": _serialize_node(n), "confidence": conf}
        for n, conf in storage.get_callees_with_confidence(node_id)
    ]

    type_refs = [_serialize_node(n) for n in storage.get_type_refs(node_id)]

    process_memberships = storage.get_process_memberships([node_id])

    return {
        "node": _serialize_node(node),
        "callers": callers,
        "callees": callees,
        "typeRefs": type_refs,
        "processMemberships": process_memberships,
    }


@router.get("/overview")
def get_overview(request: Request) -> dict:
    """Return aggregate counts of nodes by label, edges by type, and totals."""
    storage = request.app.state.storage

    nodes_by_label: dict[str, int] = {}
    total_nodes = 0
    try:
        rows = storage.execute_raw(
            "MATCH (n) RETURN labels(n), count(n) ORDER BY count(n) DESC"
        )
        for row in rows or []:
            raw_label = row[0] if row else "Unknown"
            if isinstance(raw_label, list) and raw_label:
                label = raw_label[0].lower()
            else:
                label = str(raw_label).lower()
            count = row[1] if len(row) > 1 else 0
            nodes_by_label[label] = count
            total_nodes += count
    except Exception:
        logger.warning("Failed to query node counts", exc_info=True)

    edges_by_type: dict[str, int] = {}
    total_edges = 0
    try:
        rows = storage.execute_raw(
            "MATCH ()-[r:CodeRelation]->() RETURN r.rel_type, count(r) ORDER BY count(r) DESC"
        )
        for row in rows or []:
            rel_type = row[0] if row else "Unknown"
            count = row[1] if len(row) > 1 else 0
            edges_by_type[str(rel_type)] = count
            total_edges += count
    except Exception:
        logger.warning("Failed to query edge counts", exc_info=True)

    return {
        "nodesByLabel": nodes_by_label,
        "edgesByType": edges_by_type,
        "totalNodes": total_nodes,
        "totalEdges": total_edges,
    }
