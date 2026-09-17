"""AutoHypergraph.search must forward source_ids/tags scope to the helpers."""

from typing import List

from pydantic import BaseModel, Field

from hyperextract.types import AutoHypergraph


class _Entity(BaseModel):
    name: str
    type: str = "x"


class _HyperRelation(BaseModel):
    participants: List[str]
    relation_type: str


def _hypergraph(llm_client, embedder):
    hg = AutoHypergraph(
        node_schema=_Entity,
        edge_schema=_HyperRelation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.relation_type}_{sorted(x.participants)}",
        nodes_in_edge_extractor=lambda x: tuple(x.participants),
        llm_client=llm_client,
        embedder=embedder,
    )
    hg._node_memory.add([_Entity(name="Apple")])
    hg._edge_memory.add(
        [_HyperRelation(participants=["Apple", "Steve"], relation_type="founded_by")]
    )
    hg.build_index()
    return hg


def test_search_forwards_scope(llm_client, embedder):
    hg = _hypergraph(llm_client, embedder)

    seen = {}
    hg.search_nodes = lambda query, **kw: seen.setdefault("nodes", kw) or []
    hg.search_edges = lambda query, **kw: seen.setdefault("edges", kw) or []

    hg.search("q", source_ids=["s1"], tags=["t1"])

    assert seen["nodes"]["source_ids"] == ["s1"]
    assert seen["nodes"]["tags"] == ["t1"]
    assert seen["edges"]["source_ids"] == ["s1"]
    assert seen["edges"]["tags"] == ["t1"]
