"""Tests for Graph_RAG.search return contract."""

from tests.mocks import MockChatModel, MockEmbeddings
from hyperextract.methods.rag import Graph_RAG
from hyperextract.methods.rag.graph_rag import NodeSchema, EdgeSchema


def _rag():
    rag = Graph_RAG(llm_client=MockChatModel(), embedder=MockEmbeddings())
    rag._node_memory.add([NodeSchema(name="Apple", type="org", description="d")])
    rag._edge_memory.add(
        [EdgeSchema(source="Apple", target="Steve", description="d", strength=5)]
    )
    rag.build_index()
    return rag


def test_search_default_returns_three_tuple():
    """Default (use_community=False) search must match the 3-tuple contract."""
    result = _rag().search("Apple")

    assert len(result) == 3
    nodes, edges, context = result  # must not raise
    assert context is None
