"""Build and maintain vector indexes for memory nodes.

The primary entry-point is :func:`index_memory_nodes` which groups nodes
by (type, field), lazily creates vector indexes, and fans out embedding
work across parallel async tasks.

Concurrency is controlled by the MFLOW_EMBEDDING_CONCURRENCY environment
variable (default: 20) to avoid overwhelming external embedding APIs.
"""

from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from m_flow.adapters.vector import get_vector_provider
from m_flow.core import MemoryNode
from m_flow.shared.logging_utils import get_logger

_log = get_logger("index_memory_nodes")

# Env-var names for feature flags
_SKIP_SUMMARY_ENV = "MFLOW_SKIP_TEXTSUMMARY_INDEX"
_EMBEDDING_CONCURRENCY_ENV = "MFLOW_EMBEDDING_CONCURRENCY"
_TRUTHY = frozenset({"1", "true", "yes", "y", "on"})

# Default embedding concurrency limit
_DEFAULT_EMBEDDING_CONCURRENCY = 20


def _get_embedding_concurrency() -> int:
    """Return the embedding concurrency limit from env or default."""
    try:
        return int(os.getenv(_EMBEDDING_CONCURRENCY_ENV, str(_DEFAULT_EMBEDDING_CONCURRENCY)))
    except ValueError:
        return _DEFAULT_EMBEDDING_CONCURRENCY


# ── feature flag ──────────────────────────────────────────────────────


def _should_skip_textsummary_index() -> bool:
    """Return *True* when FragmentDigest vector indexing is disabled."""
    return os.getenv(_SKIP_SUMMARY_ENV, "true").lower() in _TRUTHY


# ── grouping / batching helpers ───────────────────────────────────────

# Mapping shape: type_name -> field_name -> [memory_node_copy, ...]
_GroupedNodes = Dict[str, Dict[str, List[MemoryNode]]]


def _prepare_node_copy(node: MemoryNode, field: str) -> MemoryNode:
    """Duplicate *node* with metadata narrowed to a single index field."""
    clone = node.model_copy()
    # Isolate metadata to prevent mutation of shared class-level default
    clone.metadata = {"index_fields": [field]}
    return clone


async def _group_by_type_and_field(
    nodes: List[MemoryNode],
    vec_engine,
    skip_digest: bool,
) -> _GroupedNodes:
    """Partition *nodes* into ``{type: {field: [copies]}}`` buckets.

    Vector indexes are created lazily the first time a (type, field)
    pair is encountered.
    """
    groups: _GroupedNodes = defaultdict(dict)
    created_indexes: Set[Tuple[str, str]] = set()

    for nd in nodes:
        cls_name = type(nd).__name__

        # Feature flag: skip FragmentDigest embedding when configured
        if skip_digest and cls_name == "FragmentDigest":
            continue

        for fld in nd.metadata.get("index_fields", []):
            if getattr(nd, fld, None) is None:
                continue

            key = (cls_name, fld)
            if key not in created_indexes:
                await vec_engine.create_vector_index(cls_name, fld)
                created_indexes.add(key)
                groups[cls_name][fld] = []

            groups[cls_name][fld].append(_prepare_node_copy(nd, fld))

    return groups


def _split_into_batches(
    groups: _GroupedNodes,
    max_batch: int,
):
    """Yield ``(type_name, field_name, chunk)`` tuples of bounded size."""
    for type_name, fields in groups.items():
        for field_name, items in fields.items():
            offset = 0
            while offset < len(items):
                yield type_name, field_name, items[offset : offset + max_batch]
                offset += max_batch


# ── public: vector indexing ───────────────────────────────────────────


async def index_memory_nodes(memory_nodes: list[MemoryNode]):
    """Create or update vector embeddings for every indexable field.

    Parameters
    ----------
    memory_nodes:
        Nodes whose ``metadata["index_fields"]`` lists the field names
        that should be embedded into the vector store.

    Returns
    -------
    list[MemoryNode]
        Pass-through of the original *memory_nodes* for pipeline chaining.

    Notes
    -----
    Concurrency is limited by MFLOW_EMBEDDING_CONCURRENCY (default: 20)
    to avoid overwhelming external embedding APIs. Failed batches are
    logged but do not abort the entire operation.
    """
    vec = get_vector_provider()
    skip_digest = _should_skip_textsummary_index()

    grouped = await _group_by_type_and_field(memory_nodes, vec, skip_digest)

    chunk_size = vec.embedding_engine.get_batch_size()
    concurrency = _get_embedding_concurrency()
    semaphore = asyncio.Semaphore(concurrency)

    batches = list(_split_into_batches(grouped, chunk_size))
    total_batches = len(batches)

    if total_batches > 0:
        _log.info(
            f"[index_memory_nodes] Starting {total_batches} embedding batches "
            f"(concurrency={concurrency}, batch_size={chunk_size})"
        )

    success_count = 0
    fail_count = 0

    async def _bounded_index(tname: str, fname: str, chunk: list, batch_id: int):
        """Run vec.index_memory_nodes with semaphore-bounded concurrency."""
        nonlocal success_count, fail_count
        async with semaphore:
            try:
                await vec.index_memory_nodes(tname, fname, chunk)
                success_count += 1
                if batch_id % 50 == 0 or batch_id == total_batches - 1:
                    _log.info(
                        f"[index_memory_nodes] Progress: {success_count + fail_count}/{total_batches} "
                        f"(success={success_count}, failed={fail_count})"
                    )
            except Exception as e:
                fail_count += 1
                _log.error(
                    f"[index_memory_nodes] Batch {batch_id} failed ({tname}.{fname}, "
                    f"{len(chunk)} nodes): {type(e).__name__}: {str(e)[:100]}"
                )

    tasks = [
        asyncio.create_task(_bounded_index(tname, fname, chunk, idx))
        for idx, (tname, fname, chunk) in enumerate(batches)
    ]

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
        _log.info(f"[index_memory_nodes] Complete: {success_count}/{total_batches} succeeded, {fail_count} failed")

    return memory_nodes


# ── public: recursive model traversal ─────────────────────────────────


async def get_memory_nodes_from_model(
    root: MemoryNode,
    added_memory_nodes: Optional[Dict[str, bool]] = None,
    visited_properties: Optional[Dict[str, bool]] = None,
) -> List[MemoryNode]:
    """Recursively collect all ``MemoryNode`` instances reachable from *root*.

    Traverses scalar and list fields, deduplicating by node id so each
    node appears at most once in the returned list.  The *root* itself is
    appended last (depth-first post-order).
    """
    collected: List[MemoryNode] = []
    seen_ids = added_memory_nodes if added_memory_nodes is not None else {}
    seen_props = visited_properties if visited_properties is not None else {}

    for attr_name, attr_val in root:
        targets: List[MemoryNode] = []

        if isinstance(attr_val, MemoryNode):
            targets = [attr_val]
        elif isinstance(attr_val, list) and attr_val and isinstance(attr_val[0], MemoryNode):
            targets = attr_val

        for child in targets:
            prop_key = f"{root.id}{attr_name}{child.id}"
            if prop_key in seen_props:
                return []
            seen_props[prop_key] = True

            descendants = await get_memory_nodes_from_model(
                child,
                added_memory_nodes=seen_ids,
                visited_properties=seen_props,
            )
            for desc in descendants:
                nid = str(desc.id)
                if nid not in seen_ids:
                    seen_ids[nid] = True
                    collected.append(desc)

    # Append root node itself if not yet seen
    root_id = str(root.id)
    if root_id not in seen_ids:
        collected.append(root)

    return collected
