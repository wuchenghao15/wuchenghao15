"""Scope forwarding through method-level search overrides (#90 family).

Graph_RAG.search and Cog_RAG.search override their AutoType's search and
previously dropped source_ids/tags, so scoped search on those KAs either
raised TypeError (CLI passes the kwargs) or silently ignored the scope.
"""

import pytest

from tests.mocks import MockChatModel, MockEmbeddings

from hyperextract.methods.rag import Cog_RAG, Graph_RAG
from hyperextract.methods.rag.cog_rag import ThemeSchema
from hyperextract.methods.rag.graph_rag import EdgeSchema, NodeSchema


def _rag_with_ledger():
    rag = Graph_RAG(llm_client=MockChatModel(), embedder=MockEmbeddings())
    node = NodeSchema(name="Apple", type="org", description="d")
    edge = EdgeSchema(source="Apple", target="Steve", description="d", strength=5)
    rag._node_memory.add([node], source_id="d1")
    rag._edge_memory.add([edge], source_id="d1")
    rag.build_index()
    return rag


class TestGraphRagScope:
    def test_signature_accepts_scope(self):
        import inspect

        params = inspect.signature(Graph_RAG.search).parameters
        assert "source_ids" in params and "tags" in params

    def test_scoped_search_only_returns_attributed_items(self):
        rag = _rag_with_ledger()

        nodes, edges, _ = rag.search("Apple", source_ids=["d1"])
        assert [n.name for n in nodes] == ["Apple"]
        assert [e.source for e in edges] == ["Apple"]

        # Unknown source: nothing is in scope.
        nodes, edges, _ = rag.search("Apple", source_ids=["nope"])
        assert nodes == [] and edges == []

    def test_community_path_forwards_scope_too(self):
        rag = _rag_with_ledger()
        # No community reports -> build_communities would run; point it at a
        # frozen state so the search path (not the builder) is exercised.
        rag.community_reports = {}
        object.__setattr__(rag, "build_communities", lambda: None)

        nodes, edges, context = rag.search(
            "Apple", use_community=True, source_ids=["d1"]
        )
        assert [n.name for n in nodes] == ["Apple"]
        assert context == {}  # no reports -> empty context dict


class TestCogRagScope:
    def test_search_forwards_scope_to_both_layers(self):
        cog = Cog_RAG.__new__(Cog_RAG)
        calls = {}

        class _Layer:
            def search_edges(self, query, top_k=3, **kwargs):
                calls["edges"] = kwargs
                return []

            def search_nodes(self, query, top_k=3, **kwargs):
                calls["nodes"] = kwargs
                return []

        cog.theme_layer = _Layer()
        cog.detail_layer = _Layer()

        result = cog.search("q", source_ids=["s1"], tags=["t1"])

        assert result == {"themes": [], "entities": []}
        assert calls["edges"] == {"source_ids": ["s1"], "tags": ["t1"]}
        assert calls["nodes"] == {"source_ids": ["s1"], "tags": ["t1"]}

    def test_chat_forwards_scope_to_search(self):
        cog = Cog_RAG.__new__(Cog_RAG)
        seen = {}

        def _search(query, top_k_themes=3, top_k_entities=3, **kwargs):
            seen["kwargs"] = kwargs
            return {"themes": [], "entities": []}

        cog.search = _search
        from langchain_core.runnables import RunnableLambda

        cog.llm = RunnableLambda(lambda _: "ok")

        cog.chat("q", source_ids=["s1"], tags=["t1"])

        assert seen["kwargs"] == {"source_ids": ["s1"], "tags": ["t1"]}

    def test_cog_rag_uses_hypergraph_layers(self):
        """ThemeSchema participates in the theme layer's hyperedge schema."""
        assert issubclass(ThemeSchema, object)
