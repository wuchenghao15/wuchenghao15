"""
MemoryGraph – in-memory graph materialised from a persistent store.

The graph is populated via :pymeth:`project_graph_from_db` which pulls
node / edge data through a :class:`GraphProvider` adapter and rebuilds
a local adjacency structure suitable for vector-distance scoring and
top-k triplet extraction.
"""

from __future__ import annotations

import heapq
import time
from typing import Dict, List, Optional, Type, Union

from m_flow.adapters.graph.graph_db_interface import GraphProvider
from m_flow.knowledge.graph_ops.exceptions import (
    ConceptAlreadyExistsError,
    ConceptNotFoundError,
    InvalidDimensionsError,
)
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryAbstractGraph import MemoryAbstractGraph
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge, Node
from m_flow.shared.logging_utils import get_logger

_log = get_logger("MemoryGraph")


class MemoryGraph(MemoryAbstractGraph):
    """
    Materialised graph that lives entirely in process memory.

    Nodes are indexed by their string identifier in a dictionary for O(1)
    look-up; edges are stored in insertion order inside a flat list.  The
    ``directed`` flag controls whether edge semantics are symmetric.
    """

    __slots__ = ("nodes", "edges", "directed")

    nodes: Dict[str, Node]
    edges: List[Edge]
    directed: bool

    def __init__(self, directed: bool = True):
        self.nodes = {}
        self.edges = []
        self.directed = directed

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_node(self, node: Node) -> None:
        existing = self.nodes.get(node.id)
        if existing is not None:
            raise ConceptAlreadyExistsError(message=f"Duplicate node insertion blocked – id={node.id}")
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)
        edge.node1.add_skeleton_edge(edge)
        edge.node2.add_skeleton_edge(edge)

    # ------------------------------------------------------------------
    # Look-ups
    # ------------------------------------------------------------------

    def get_node(self, node_id: str) -> Node:
        return self.nodes.get(node_id, None)

    def get_edges_from_node(self, node_id: str) -> List[Edge]:
        target_node = self.get_node(node_id)
        if target_node is None:
            raise ConceptNotFoundError(message=f"Cannot retrieve edges – no node with id={node_id}")
        return target_node.skeleton_edges

    def get_edges(self) -> List[Edge]:
        return self.edges

    # ------------------------------------------------------------------
    # Sub-graph retrieval strategies
    # ------------------------------------------------------------------

    async def _extract_typed_subgraph(
        self,
        adapter,
        node_type,
        node_name,
        relevant_ids_to_filter=None,
        strict_nodeset_filtering: bool = False,
    ):
        """
        Pull a sub-graph scoped to a specific node-set.

        When *relevant_ids_to_filter* is supplied **and** the adapter
        exposes an id-constrained nodeset query, that path is tried first.
        ``strict_nodeset_filtering=True`` prevents falling through to the
        unconstrained nodeset query when the id-filter yields nothing
        (useful for episodic retrieval where an empty result is meaningful).
        """
        _log.info("Fetching nodeset-scoped sub-graph from adapter.")

        if relevant_ids_to_filter and hasattr(adapter, "get_nodeset_id_filtered_graph_data"):
            vertex_rows, link_rows = await adapter.get_nodeset_id_filtered_graph_data(
                node_type=node_type,
                node_name=node_name,
                target_ids=relevant_ids_to_filter,
            )
            if vertex_rows and link_rows:
                return vertex_rows, link_rows

            if strict_nodeset_filtering:
                _log.info("ID-constrained nodeset empty; strict mode – returning nothing.")
                return [], []

            _log.info("ID-constrained nodeset empty; falling back to full nodeset query.")

        vertex_rows, link_rows = await adapter.extract_typed_subgraph(node_type=node_type, node_name=node_name)
        if not vertex_rows or not link_rows:
            raise ConceptNotFoundError(message="Nodeset query returned no data – the set may not exist in the store.")
        return vertex_rows, link_rows

    async def _get_full_or_id_filtered_graph(
        self,
        adapter,
        relevant_ids_to_filter,
    ):
        """Load the complete graph or a subset filtered by node identifiers."""
        if relevant_ids_to_filter is None:
            _log.info("Loading complete graph from persistence layer.")
            vertex_rows, link_rows = await adapter.get_graph_data()
            if not vertex_rows or not link_rows:
                raise ConceptNotFoundError(message="Persistence layer returned an empty graph.")
            return vertex_rows, link_rows

        id_query_fn = getattr(adapter, "get_id_filtered_graph_data", adapter.get_graph_data)
        adapter_supports_id_filter = getattr(adapter.__class__, "get_id_filtered_graph_data", None) is not None

        if adapter_supports_id_filter:
            _log.info("Requesting id-filtered projection from adapter.")
            vertex_rows, link_rows = await id_query_fn(target_ids=relevant_ids_to_filter)
        else:
            _log.info("Adapter lacks id-filter support; loading full graph instead.")
            vertex_rows, link_rows = await id_query_fn()

        if adapter_supports_id_filter and (not vertex_rows or not link_rows):
            _log.warning("ID-filtered projection was empty; retrying with full graph.")
            vertex_rows, link_rows = await adapter.get_graph_data()

        if not vertex_rows or not link_rows:
            raise ConceptNotFoundError("Graph projection yielded no vertices or links.")
        return vertex_rows, link_rows

    async def _get_filtered_graph(
        self,
        adapter,
        memory_fragment_filter,
    ):
        """Retrieve a sub-graph constrained by attribute predicates."""
        _log.info("Applying attribute-based filter for graph retrieval.")
        vertex_rows, link_rows = await adapter.query_by_attributes(attribute_filters=memory_fragment_filter)
        if not vertex_rows or not link_rows:
            raise ConceptNotFoundError(message="Attribute-filtered projection returned no data.")
        return vertex_rows, link_rows

    # ------------------------------------------------------------------
    # Projection entry-point
    # ------------------------------------------------------------------

    async def project_graph_from_db(
        self,
        adapter: Union[GraphProvider],
        node_properties_to_project: List[str],
        edge_properties_to_project: List[str],
        directed=True,
        node_dimension=1,
        edge_dimension=1,
        memory_fragment_filter=[],
        node_type: Optional[Type] = None,
        node_name: Optional[List[str]] = None,
        relevant_ids_to_filter: Optional[List[str]] = None,
        triplet_distance_penalty: float = 3.5,
        strict_nodeset_filtering: bool = False,
    ) -> None:
        """
        Materialise a graph from a persistent store into this object.

        The method selects a retrieval strategy based on the combination of
        *node_type*, *memory_fragment_filter*, and *relevant_ids_to_filter*,
        then populates :pyattr:`nodes` and :pyattr:`edges`.

        Raises :class:`InvalidDimensionsError` when either dimension is < 1.
        """
        if node_dimension < 1 or edge_dimension < 1:
            raise InvalidDimensionsError()

        try:
            # --- choose retrieval strategy ---
            if node_type is not None and node_name not in [None, [], ""]:
                vertex_rows, link_rows = await self._extract_typed_subgraph(
                    adapter,
                    node_type,
                    node_name,
                    relevant_ids_to_filter=relevant_ids_to_filter,
                    strict_nodeset_filtering=strict_nodeset_filtering,
                )
            elif len(memory_fragment_filter) == 0:
                vertex_rows, link_rows = await self._get_full_or_id_filtered_graph(adapter, relevant_ids_to_filter)
            else:
                vertex_rows, link_rows = await self._get_filtered_graph(adapter, memory_fragment_filter)

            t_start = time.monotonic()

            # --- hydrate nodes ---
            for vid, props in vertex_rows:
                projected_attrs = {attr_key: props.get(attr_key) for attr_key in node_properties_to_project}
                self.add_node(
                    Node(
                        str(vid),
                        projected_attrs,
                        dimension=node_dimension,
                        node_penalty=triplet_distance_penalty,
                    )
                )

            # --- hydrate edges ---
            for src_id, dst_id, rel_type, props in link_rows:
                src_vertex = self.get_node(str(src_id))
                dst_vertex = self.get_node(str(dst_id))
                if src_vertex is None or dst_vertex is None:
                    raise ConceptNotFoundError(
                        message=(f"Link ({src_id} -> {dst_id}) references a vertex absent from the projection")
                    )
                link_attrs = {attr_key: props.get(attr_key) for attr_key in edge_properties_to_project}
                link_attrs["relationship_type"] = rel_type

                self.add_edge(
                    Edge(
                        src_vertex,
                        dst_vertex,
                        attributes=link_attrs,
                        directed=directed,
                        dimension=edge_dimension,
                        edge_penalty=triplet_distance_penalty,
                    )
                )

            elapsed_sec = time.monotonic() - t_start
            _log.info(
                "Projection complete",
                extra={
                    "vertex_count": len(self.nodes),
                    "link_count": len(self.edges),
                    "elapsed_s": f"{elapsed_sec:.2f}",
                },
            )

        except Exception as exc:
            _log.error("Graph projection failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Vector-distance mapping
    # ------------------------------------------------------------------

    async def map_vector_distances_to_graph_nodes(self, node_distances) -> None:
        mapped_count = 0
        for _category, scored_hits in node_distances.items():
            for hit in scored_hits:
                nid = str(hit.id)
                vertex = self.get_node(nid)
                if vertex is not None:
                    vertex.add_attribute("vector_distance", hit.score)
                    mapped_count += 1

    async def map_vector_distances_to_graph_edges(self, edge_distances) -> None:
        try:
            if edge_distances is None:
                return

            score_lookup = {entry.payload["text"]: entry.score for entry in edge_distances}

            for link in self.edges:
                descriptor = link.attributes.get("edge_text") or link.attributes.get("relationship_type")
                matched_score = score_lookup.get(descriptor)
                if matched_score is not None:
                    link.attributes["vector_distance"] = matched_score

        except Exception as err:
            _log.error("Failed to map vector distances onto edges: %s", err)
            raise err

    # ------------------------------------------------------------------
    # Triplet importance ranking
    # ------------------------------------------------------------------

    async def calculate_top_triplet_importances(self, k: int) -> List[Edge]:
        def _triplet_cost(link: Edge) -> float:
            d_src = link.node1.attributes.get("vector_distance", 1)
            d_dst = link.node2.attributes.get("vector_distance", 1)
            d_link = link.attributes.get("vector_distance", 1)
            return d_src + d_dst + d_link

        return heapq.nsmallest(k, self.edges, key=_triplet_cost)
