"""Contract: AutoGraph and AutoHypergraph share GraphIndexMixin methods."""

from pydantic import BaseModel, Field

from hyperextract.types import AutoGraph, AutoHypergraph
from hyperextract.types.graph import GraphIndexMixin


class Entity(BaseModel):
    name: str
    type: str = "ENTITY"
    properties: dict = Field(default_factory=dict)


class Relation(BaseModel):
    source: str
    target: str
    relation_type: str


def test_graph_and_hypergraph_share_index_function_objects():
    assert AutoGraph.merge_batch_data is AutoHypergraph.merge_batch_data
    assert AutoGraph.build_index is AutoHypergraph.build_index
    assert AutoGraph.build_node_index is AutoHypergraph.build_node_index
    assert AutoGraph.build_edge_index is AutoHypergraph.build_edge_index
    assert AutoGraph.search is AutoHypergraph.search
    assert AutoGraph.search_nodes is AutoHypergraph.search_nodes
    assert AutoGraph.search_edges is AutoHypergraph.search_edges
    assert AutoGraph.search is GraphIndexMixin.search
    assert AutoHypergraph.search is GraphIndexMixin.search


def test_public_search_still_returns_nodes_edges_tuple(llm_client, embedder):
    graph = AutoGraph(
        node_schema=Entity,
        edge_schema=Relation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=llm_client,
        embedder=embedder,
    )
    graph._node_memory.add([Entity(name="Apple")])
    graph._edge_memory.add(
        [Relation(source="Apple", target="Steve Jobs", relation_type="founded_by")]
    )
    graph.build_index()

    result = graph.search("Apple", top_k=1)
    assert isinstance(result, tuple)
    assert len(result) == 2
    nodes, edges = result
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    assert not hasattr(result, "kind")
    assert not hasattr(result, "payload")
