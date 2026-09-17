"""Persist memory nodes into the graph store with vector indexing.

Entry-point: :func:`persist_memory_nodes` — validates incoming nodes, fans
out graph extraction in parallel, deduplicates the resulting sub-graphs,
commits to the graph engine, and refreshes both node and edge vector
indexes.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Set, Tuple

from m_flow.adapters.graph import get_graph_provider
from m_flow.core import MemoryNode
from m_flow.core.domain.models import MemoryTriplet
from m_flow.core.domain.utils import generate_node_id
from m_flow.knowledge.graph_ops.utils import (
    deduplicate_nodes_and_edges,
    extract_graph,
)
from m_flow.shared.logging_utils import get_logger
from m_flow.storage.exceptions import InvalidMemoryNodesInAddMemoryNodesError

from .index_graph_links import index_relations
from .index_memory_nodes import index_memory_nodes

_log = get_logger("persist_memory_nodes")

# ── input validation ──────────────────────────────────────────────────


def _validate_input(memory_nodes: object) -> None:
    """Raise when *memory_nodes* is not a list of ``MemoryNode``."""
    if not isinstance(memory_nodes, list):
        raise InvalidMemoryNodesInAddMemoryNodesError("memory_nodes must be a list.")
    for item in memory_nodes:
        if not isinstance(item, MemoryNode):
            raise InvalidMemoryNodesInAddMemoryNodesError("memory_nodes: each item must be a MemoryNode.")


# ── graph extraction ──────────────────────────────────────────────────


async def _extract_subgraphs(
    memory_nodes: List[MemoryNode],
) -> Tuple[list, list]:
    """Fan-out graph extraction and merge all sub-graphs.

    Returns the deduplicated (nodes, edges) pair.
    """
    seen_nodes: Dict = {}
    seen_edges: Dict = {}
    seen_props: Dict = {}

    extraction_coros = [
        extract_graph(
            node,
            added_nodes=seen_nodes,
            added_edges=seen_edges,
            visited_properties=seen_props,
        )
        for node in memory_nodes
    ]
    raw_results = await asyncio.gather(*extraction_coros)

    all_nodes: list = []
    all_edges: list = []
    for n_batch, e_batch in raw_results:
        all_nodes.extend(n_batch)
        all_edges.extend(e_batch)

    return deduplicate_nodes_and_edges(all_nodes, all_edges)


# ── persistence ───────────────────────────────────────────────────────


async def _commit_to_graph(
    graph_engine,
    nodes: list,
    edges: list,
    extra_edges: Optional[List] = None,
) -> list:
    """Write nodes and edges to the graph engine and update indexes.

    The execution order is designed to ensure graph integrity:
    1. First write all graph structure (nodes + edges)
    2. Then perform vector indexing

    This ensures that even if vector indexing fails, the graph structure
    is complete and the data can be queried (without vector search).
    """
    # Step 1: Write all graph structure first
    _log.info(f"[commit] Phase 1: Writing graph structure ({len(nodes)} nodes, {len(edges)} edges)")
    await graph_engine.add_nodes(nodes)
    await graph_engine.add_edges(edges)

    if extra_edges:
        _, deduped_extra = deduplicate_nodes_and_edges([], extra_edges)
        await graph_engine.add_edges(deduped_extra)
        edges.extend(deduped_extra)
        _log.info(f"[commit] Added {len(extra_edges)} extra edges")

    _log.info("[commit] Phase 1 complete: Graph structure written successfully")

    # Step 2: Vector indexing (failure here won't affect graph integrity)
    _log.info("[commit] Phase 2: Starting vector indexing")
    try:
        await index_memory_nodes(nodes)
        _log.info("[commit] Node vector indexing complete")
    except Exception as e:
        _log.error(f"[commit] Node vector indexing failed: {type(e).__name__}: {str(e)[:100]}")
        _log.warning("[commit] Graph structure is intact, but vector search may be incomplete")

    try:
        await index_relations(edges)
        _log.info("[commit] Edge vector indexing complete")
    except Exception as e:
        _log.error(f"[commit] Edge vector indexing failed: {type(e).__name__}: {str(e)[:100]}")
        _log.warning("[commit] Graph structure is intact, but edge vector search may be incomplete")

    _log.info("[commit] Phase 2 complete")

    return edges


# ── triplet helpers ───────────────────────────────────────────────────


def _extract_embeddable_text_from_datapoint(memory_node: MemoryNode) -> str:
    """Collect indexable field values from *memory_node* into a single string."""
    if memory_node is None or not hasattr(memory_node, "metadata"):
        return ""

    fields_to_embed = memory_node.metadata.get("index_fields", [])
    if not fields_to_embed:
        return ""

    parts = (str(getattr(memory_node, fname, None) or "").strip() for fname in fields_to_embed)
    return " ".join(p for p in parts if p)


def _build_node_index(nodes: List[MemoryNode]) -> Dict[str, MemoryNode]:
    """Map node-id → MemoryNode for fast lookup (first occurrence wins)."""
    index: Dict[str, MemoryNode] = {}
    for nd in nodes:
        nid = str(getattr(nd, "id", ""))
        if nid and nid not in index:
            index[nid] = nd
    return index


def _resolve_relationship_label(
    rel_name: Optional[str],
    props: Optional[dict],
) -> str:
    """Determine the best human-readable label for an edge."""
    if isinstance(props, dict):
        custom = props.get("edge_text")
        if isinstance(custom, str) and custom.strip():
            return custom.strip()
    return rel_name or ""


def _create_triplets_from_graph(
    nodes: List[MemoryNode],
    edges: List[tuple],
) -> List[MemoryTriplet]:
    """Materialise ``MemoryTriplet`` objects from graph edges.

    Each valid edge is converted into a triplet whose embeddable text
    follows the pattern ``"source_text -› label -› target_text"``.
    Duplicates (by deterministic id) are skipped.
    """
    lookup = _build_node_index(nodes)
    seen: Set[str] = set()
    output: List[MemoryTriplet] = []

    for etuple in edges:
        if len(etuple) < 4:
            continue

        src_id, tgt_id, rel_name, edge_props = etuple[0], etuple[1], etuple[2], etuple[3]

        src = lookup.get(str(src_id))
        tgt = lookup.get(str(tgt_id))
        if src is None or tgt is None or rel_name is None:
            continue

        label = _resolve_relationship_label(rel_name, edge_props)
        src_text = _extract_embeddable_text_from_datapoint(src)
        tgt_text = _extract_embeddable_text_from_datapoint(tgt)

        if not src_text and not label and not rel_name:
            continue

        combined = f"{src_text} -› {label}-›{tgt_text}".strip()
        tid = generate_node_id(str(src_id) + rel_name + str(tgt_id))

        if tid in seen:
            continue
        seen.add(tid)

        output.append(
            MemoryTriplet(
                id=tid,
                from_node_id=str(src_id),
                to_node_id=str(tgt_id),
                text=combined,
            )
        )

    return output


# ── public API ────────────────────────────────────────────────────────


async def persist_memory_nodes(
    memory_nodes: List[MemoryNode],
    custom_edges: Optional[List] = None,
    embed_triplets: bool = False,
) -> List[MemoryNode]:
    """Insert *memory_nodes* into the graph with full vector indexing.

    Parameters
    ----------
    memory_nodes:
        Node objects to persist.
    custom_edges:
        Optional extra edge tuples to store alongside auto-extracted edges.
    embed_triplets:
        When ``True``, generates :class:`MemoryTriplet` embeddings from the
        resulting graph structure.

    Returns
    -------
    List[MemoryNode]
        The same *memory_nodes* list passed in (pass-through for chaining).
    """
    _validate_input(memory_nodes)

    unique_nodes, unique_edges = await _extract_subgraphs(memory_nodes)

    engine = await get_graph_provider()
    final_edges = await _commit_to_graph(
        engine,
        unique_nodes,
        unique_edges,
        extra_edges=custom_edges if isinstance(custom_edges, list) and custom_edges else None,
    )

    if embed_triplets:
        triplets = _create_triplets_from_graph(unique_nodes, final_edges)
        if triplets:
            await index_memory_nodes(triplets)
            _log.info("Created and indexed %d triplets from graph structure", len(triplets))

    return memory_nodes
