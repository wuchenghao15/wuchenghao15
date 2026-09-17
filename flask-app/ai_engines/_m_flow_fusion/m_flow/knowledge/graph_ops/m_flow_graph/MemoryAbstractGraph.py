"""Abstract protocol for in-memory graph representations.

Concrete implementations (e.g. :class:`MemoryGraph`) hold a projection of the
persistent graph and expose traversal / mutation methods consumed by the
retrieval layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from m_flow.adapters.graph.graph_db_interface import GraphProvider
    from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge, Node


class MemoryAbstractGraph(ABC):
    """Read/write interface over a projected knowledge graph."""

    # -- Mutation -------------------------------------------------------------

    @abstractmethod
    def add_node(self, node: "Node") -> None: ...

    @abstractmethod
    def add_edge(self, edge: "Edge") -> None: ...

    # -- Queries --------------------------------------------------------------

    @abstractmethod
    def get_node(self, node_id: str) -> "Node": ...

    @abstractmethod
    def get_edges(self, node_id: str) -> List["Edge"]: ...

    # -- DB projection --------------------------------------------------------

    @abstractmethod
    async def project_graph_from_db(
        self,
        adapter: "GraphProvider",
        *,
        directed: bool = True,
        dimension: int = 1,
    ) -> None:
        """Materialise the graph from the persistent store into memory."""
        ...
