"""AutoGraph / AutoHypergraph.chat must forward source_ids/tags to search helpers."""

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel

from hyperextract.types import AutoGraph, AutoHypergraph


class _Entity(BaseModel):
    name: str
    type: str = "x"


class _Relation(BaseModel):
    source: str
    target: str
    relation_type: str = "related"


class _HyperRelation(BaseModel):
    participants: list[str]
    relation_type: str


def _graph(llm_client, embedder):
    return AutoGraph(
        node_schema=_Entity,
        edge_schema=_Relation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=llm_client,
        embedder=embedder,
    )


def _hypergraph(llm_client, embedder):
    return AutoHypergraph(
        node_schema=_Entity,
        edge_schema=_HyperRelation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.relation_type}_{sorted(x.participants)}",
        nodes_in_edge_extractor=lambda x: tuple(x.participants),
        llm_client=llm_client,
        embedder=embedder,
    )


def test_autograph_chat_forwards_scope(llm_client, embedder):
    ka = _graph(llm_client, embedder)
    seen = {}

    def _nodes(query, **kw):
        seen["nodes"] = kw
        return []

    def _edges(query, **kw):
        seen["edges"] = kw
        return []

    ka.search_nodes = _nodes
    ka.search_edges = _edges
    ka.llm_client = RunnableLambda(lambda _: AIMessage(content="ok"))

    ka.chat("q", source_ids=["s1"], tags=["t1"])

    assert seen["nodes"]["source_ids"] == ["s1"]
    assert seen["nodes"]["tags"] == ["t1"]
    assert seen["edges"]["source_ids"] == ["s1"]
    assert seen["edges"]["tags"] == ["t1"]


def test_autohypergraph_chat_forwards_scope(llm_client, embedder):
    ka = _hypergraph(llm_client, embedder)
    seen = {}

    def _nodes(query, **kw):
        seen["nodes"] = kw
        return []

    def _edges(query, **kw):
        seen["edges"] = kw
        return []

    ka.search_nodes = _nodes
    ka.search_edges = _edges
    ka.llm_client = RunnableLambda(lambda _: AIMessage(content="ok"))

    ka.chat("q", source_ids=["s1"], tags=["t1"])

    assert seen["nodes"]["source_ids"] == ["s1"]
    assert seen["nodes"]["tags"] == ["t1"]
    assert seen["edges"]["source_ids"] == ["s1"]
    assert seen["edges"]["tags"] == ["t1"]
