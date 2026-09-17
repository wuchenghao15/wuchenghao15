"""Build and persist vector indices for graph relationship types.

Scans edge tuples, aggregates unique relationship labels with occurrence
counts, wraps each label in a ``RelationType`` node, and delegates the
embedding work to :func:`index_memory_nodes`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from m_flow.adapters.graph import get_graph_provider
from m_flow.adapters.graph.graph_db_interface import EdgeTuple as EdgeData
from m_flow.core.domain.utils.generate_edge_id import generate_edge_id
from m_flow.knowledge.graph_ops.models.RelationType import RelationType
from m_flow.shared.logging_utils import get_logger
from m_flow.storage.index_memory_nodes import index_memory_nodes

_log = get_logger()

# ── helpers ────────────────────────────────────────────────────────────

_LABEL_KEYS: Tuple[str, ...] = ("edge_text", "relationship_name")


def _extract_label(record: dict) -> str:
    """Return the best available label string from an edge property dict."""
    for key in _LABEL_KEYS:
        val = record.get(key)
        if val:
            return val
    return ""


def _aggregate_relationship_counts(
    raw_edges: Sequence,
) -> Dict[str, int]:
    """Walk *raw_edges* and tally each distinct relationship label."""
    counts: Dict[str, int] = {}
    for edge_tuple in raw_edges:
        for element in edge_tuple:
            if not isinstance(element, dict) or "relationship_name" not in element:
                continue
            label = _extract_label(element)
            if label:
                counts[label] = counts.get(label, 0) + 1
    return counts


def create_edge_type_datapoints(
    edges_data: Sequence,
) -> List[RelationType]:
    """Convert aggregated edge labels into ``RelationType`` memory nodes."""
    label_counts = _aggregate_relationship_counts(edges_data)
    return [
        RelationType(
            id=generate_edge_id(edge_id=label),
            relationship_name=label,
            number_of_edges=n,
        )
        for label, n in label_counts.items()
    ]


# ── main entry-point ──────────────────────────────────────────────────


async def index_relations(
    edges_data: Union[
        List[EdgeData],
        List[Tuple[str, str, str, Optional[Dict[str, Any]]]],
        None,
    ] = None,
) -> None:
    """Create / refresh vector embeddings for relationship types.

    When *edges_data* is supplied directly the function skips the graph
    look-up and processes the given tuples.  Passing ``None`` (default)
    triggers a **deprecated** fall-back that fetches every edge from the
    graph engine.

    Raises
    ------
    RuntimeError
        If the graph engine cannot be initialised.
    """
    if edges_data is None:
        try:
            engine = await get_graph_provider()
            _, edges_data = await engine.get_graph_data()
        except Exception as exc:
            _log.error("Graph engine unavailable: %s", exc)
            raise RuntimeError("Initialization error") from exc
        _log.warning("Fetching all edges at index time is deprecated — pass edges to index_relations directly.")

    relation_nodes = create_edge_type_datapoints(edges_data)
    await index_memory_nodes(relation_nodes)
