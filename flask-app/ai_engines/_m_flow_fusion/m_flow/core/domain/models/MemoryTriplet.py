"""
Subject–predicate–object triplet for the knowledge graph.

Each :class:`MemoryTriplet` links two graph nodes (identified by UUID)
through a textual predicate, forming the atomic unit of factual
knowledge stored in the memory layer.  The ``text`` field is indexed
for embedding-based retrieval of specific relationships.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import Field

from m_flow.core import MemoryNode

# Indexing configuration – the predicate text is the primary search field
_TRIPLET_INDEX: Dict[str, Any] = {"index_fields": ["text"]}


class MemoryTriplet(MemoryNode):
    """
    Atomic fact represented as a directed triple *(subject → predicate → object)*.

    ``from_node_id`` and ``to_node_id`` reference the subject and object
    graph nodes respectively, while ``text`` captures the human-readable
    predicate connecting them.

    Example::

        t = MemoryTriplet(
            text="authored",
            from_node_id="a3f1c...",
            to_node_id="b27d0...",
        )
    """

    text: str = Field(
        ...,
        description="Predicate text describing the relationship between nodes",
    )
    from_node_id: str = Field(
        ...,
        description="UUID of the subject (source) node",
    )
    to_node_id: str = Field(
        ...,
        description="UUID of the object (target) node",
    )

    # Determines which fields the indexing pipeline processes
    metadata: dict = Field(default_factory=lambda: dict(_TRIPLET_INDEX))
