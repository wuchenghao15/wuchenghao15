"""Lightweight in-memory graph elements for the retrieval projection.

:class:`Node` and :class:`Edge` are **not** Pydantic models — they are plain
objects optimised for fast traversal during bundle-search scoring.  Each carries
a ``status`` bit-vector so that multi-dimensional / multi-tenant filtering can
be applied without rebuilding the projection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np

from m_flow.knowledge.graph_ops.exceptions import (
    DimensionOutOfRangeError,
    InvalidDimensionsError,
)

_DEFAULT_PENALTY: float = 3.5


class Node:
    """A vertex in the projected knowledge graph.

    Parameters
    ----------
    node_id:
        Globally unique identifier (typically a UUID string).
    attributes:
        Arbitrary key-value metadata.  ``vector_distance`` is injected
        automatically with *node_penalty* as the default value.
    dimension:
        Width of the ``status`` bit-vector (≥1).
    node_penalty:
        Default cost when this node was **not** hit by any vector search.
    """

    __slots__ = ("id", "attributes", "_neighbours", "_edges", "status")

    def __init__(
        self,
        node_id: str,
        attributes: Optional[Dict[str, Any]] = None,
        dimension: int = 1,
        node_penalty: float = _DEFAULT_PENALTY,
    ) -> None:
        if dimension < 1:
            raise InvalidDimensionsError()
        self.id = node_id
        self.attributes: Dict[str, Any] = dict(attributes) if attributes else {}
        self.attributes.setdefault("vector_distance", node_penalty)
        self._neighbours: List[Node] = []
        self._edges: List[Edge] = []
        self.status = np.ones(dimension, dtype=np.int8)

    # -- Adjacency management -------------------------------------------------

    @property
    def skeleton_neighbours(self) -> List[Node]:
        return self._neighbours

    @property
    def skeleton_edges(self) -> List[Edge]:
        return self._edges

    def add_skeleton_edge(self, edge: Edge) -> None:
        self._edges.append(edge)
        other = edge.node2 if edge.node1 is self else edge.node1
        if other not in self._neighbours:
            self._neighbours.append(other)

    def remove_skeleton_edge(self, edge: Edge) -> None:
        try:
            self._edges.remove(edge)
        except ValueError:
            return
        other = edge.node2 if edge.node1 is self else edge.node1
        still_connected = any((e.node1 is other or e.node2 is other) for e in self._edges)
        if not still_connected and other in self._neighbours:
            self._neighbours.remove(other)

    def add_skeleton_neighbor(self, neighbour: Node) -> None:
        if neighbour not in self._neighbours:
            self._neighbours.append(neighbour)

    def remove_skeleton_neighbor(self, neighbour: Node) -> None:
        if neighbour in self._neighbours:
            self._neighbours.remove(neighbour)

    # -- Dimension status -----------------------------------------------------

    def is_node_alive_in_dimension(self, dim: int) -> bool:
        if dim < 0 or dim >= self.status.size:
            raise DimensionOutOfRangeError(dimension=dim, max_index=self.status.size - 1)
        return bool(self.status[dim])

    # -- Attribute helpers ----------------------------------------------------

    def add_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def get_attribute(self, key: str) -> Union[str, int, float]:
        return self.attributes[key]

    def get_skeleton_edges(self) -> List[Edge]:
        return self._edges

    def get_skeleton_neighbours(self) -> List[Node]:
        return self._neighbours

    # -- Dunder ---------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<Node {self.id!r}>"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Node) and self.id == other.id


class Edge:
    """A relationship between two :class:`Node` instances.

    Parameters
    ----------
    node1, node2:
        Source and target vertices.
    directed:
        Whether the edge has a direction (default ``True``).
    edge_penalty:
        Default cost when this edge was **not** matched by vector search.
    """

    __slots__ = ("node1", "node2", "attributes", "directed", "status")

    def __init__(
        self,
        node1: Node,
        node2: Node,
        attributes: Optional[Dict[str, Any]] = None,
        directed: bool = True,
        dimension: int = 1,
        edge_penalty: float = _DEFAULT_PENALTY,
    ) -> None:
        if dimension < 1:
            raise InvalidDimensionsError()
        self.node1 = node1
        self.node2 = node2
        self.attributes: Dict[str, Any] = dict(attributes) if attributes else {}
        self.attributes.setdefault("vector_distance", edge_penalty)
        self.directed = directed
        self.status = np.ones(dimension, dtype=np.int8)

    # -- Dimension status -----------------------------------------------------

    def is_edge_alive_in_dimension(self, dim: int) -> bool:
        if dim < 0 or dim >= self.status.size:
            raise DimensionOutOfRangeError(dimension=dim, max_index=self.status.size - 1)
        return bool(self.status[dim])

    # -- Attribute helpers ----------------------------------------------------

    def add_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def get_attribute(self, key: str) -> Optional[Union[str, int, float]]:
        return self.attributes.get(key)

    def get_source_node(self) -> Node:
        return self.node1

    def get_destination_node(self) -> Node:
        return self.node2

    # -- Dunder ---------------------------------------------------------------

    def __repr__(self) -> str:
        arrow = "->" if self.directed else "--"
        return f"<Edge {self.node1.id!r} {arrow} {self.node2.id!r}>"

    def __hash__(self) -> int:
        if self.directed:
            return hash((self.node1.id, self.node2.id))
        return hash(frozenset((self.node1.id, self.node2.id)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        if self.directed:
            return self.node1 == other.node1 and self.node2 == other.node2
        return {self.node1, self.node2} == {other.node1, other.node2}
