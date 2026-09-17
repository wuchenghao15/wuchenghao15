"""Verification suite for fine-grained triplet search in the M-Flow retrieval module."""

import pytest
from unittest.mock import AsyncMock, patch

from m_flow.retrieval.utils.fine_grained_triplet_search import (
    fine_grained_triplet_search,
    get_memory_fragment,
)
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph
from m_flow.knowledge.graph_ops.exceptions.exceptions import ConceptNotFoundError

_PATCH_ROOT = "m_flow.retrieval.utils.fine_grained_triplet_search"
_VEC_ENGINE_PATH = f"{_PATCH_ROOT}.get_vector_provider"
_FRAGMENT_PATH = f"{_PATCH_ROOT}.get_memory_fragment"
_GRAPH_ENGINE_PATH = f"{_PATCH_ROOT}.get_graph_provider"


class _HitResult:
    """Simulated scored vector hit."""

    def __init__(self, id, score, payload=None):
        self.id = id
        self.score = score
        self.payload = payload or {}


def _build_vector_engine(*, search_rv=None, embed_rv=None):
    engine = AsyncMock()
    engine.embedding_engine = AsyncMock()
    engine.embedding_engine.embed_text = AsyncMock(return_value=embed_rv if embed_rv is not None else [[0.5, 0.6, 0.7]])
    if callable(search_rv):
        engine.search = AsyncMock(side_effect=search_rv)
    else:
        fixed = search_rv if search_rv is not None else []

        async def _typed_search(collection_name, query_vector, limit=None, where_filter=None):
            return fixed

        engine.search = AsyncMock(side_effect=_typed_search, wraps=_typed_search)
    return engine


def _build_fragment(*, importance_rv=None):
    frag = AsyncMock()
    frag.map_vector_distances_to_graph_nodes = AsyncMock()
    frag.map_vector_distances_to_graph_edges = AsyncMock()
    frag.calculate_top_triplet_importances = AsyncMock(return_value=importance_rv if importance_rv is not None else [])
    return frag


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad_query", ["", None])
    async def test_rejects_blank_or_missing_query(self, bad_query):
        with pytest.raises(ValueError, match="non-blank query"):
            await fine_grained_triplet_search(query=bad_query)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad_k", [-1, 0])
    async def test_rejects_non_positive_top_k(self, bad_k):
        with pytest.raises(ValueError, match="top_k must be greater than zero"):
            await fine_grained_triplet_search(query="hello", top_k=bad_k)


# ---------------------------------------------------------------------------
# Wide-search limit behaviour
# ---------------------------------------------------------------------------


class TestWideSearchLimit:
    @pytest.mark.asyncio
    async def test_applied_in_global_mode(self):
        engine = _build_vector_engine()
        with patch(_VEC_ENGINE_PATH, return_value=engine):
            await fine_grained_triplet_search(query="sample", node_name=None, wide_search_top_k=75)
        for invocation in engine.search.call_args_list:
            assert invocation[1]["limit"] == 75

    @pytest.mark.asyncio
    async def test_none_in_filtered_mode(self):
        engine = _build_vector_engine()
        with patch(_VEC_ENGINE_PATH, return_value=engine):
            await fine_grained_triplet_search(query="sample", node_name=["NodeA"], wide_search_top_k=50)
        for invocation in engine.search.call_args_list:
            assert invocation[1]["limit"] is None

    @pytest.mark.asyncio
    async def test_defaults_to_hundred(self):
        engine = _build_vector_engine()
        with patch(_VEC_ENGINE_PATH, return_value=engine):
            await fine_grained_triplet_search(query="sample", node_name=None)
        for invocation in engine.search.call_args_list:
            assert invocation[1]["limit"] == 100


# ---------------------------------------------------------------------------
# Collection selection
# ---------------------------------------------------------------------------


class TestCollectionSelection:
    @pytest.mark.asyncio
    async def test_standard_collections_when_unspecified(self):
        engine = _build_vector_engine()
        with patch(_VEC_ENGINE_PATH, return_value=engine):
            await fine_grained_triplet_search(query="anything")
        searched = [c[1]["collection_name"] for c in engine.search.call_args_list]
        assert searched == [
            "Episode_summary",
            "Entity_name",
            "Concept_name",
            "RelationType_relationship_name",
        ]

    @pytest.mark.asyncio
    async def test_user_provided_collections(self):
        engine = _build_vector_engine()
        user_cols = ["Alpha", "Beta"]
        with patch(_VEC_ENGINE_PATH, return_value=engine):
            await fine_grained_triplet_search(query="anything", collections=user_cols)
        searched = {c[1]["collection_name"] for c in engine.search.call_args_list}
        assert searched == set(user_cols) | {"RelationType_relationship_name"}

    @pytest.mark.asyncio
    async def test_edge_collection_always_present(self):
        engine = _build_vector_engine()
        cols_without_edge = ["Entity_name", "FragmentDigest_text"]
        with patch(_VEC_ENGINE_PATH, return_value=engine):
            await fine_grained_triplet_search(query="anything", collections=cols_without_edge)
        searched = {c[1]["collection_name"] for c in engine.search.call_args_list}
        assert "RelationType_relationship_name" in searched
        assert searched == set(cols_without_edge) | {"RelationType_relationship_name"}


# ---------------------------------------------------------------------------
# Empty results
# ---------------------------------------------------------------------------


class TestEmptyResults:
    @pytest.mark.asyncio
    async def test_yields_empty_list_when_no_hits(self):
        engine = _build_vector_engine()
        with patch(_VEC_ENGINE_PATH, return_value=engine):
            outcome = await fine_grained_triplet_search(query="nothing")
        assert outcome == []


# ---------------------------------------------------------------------------
# Query embedding
# ---------------------------------------------------------------------------


class TestQueryEmbedding:
    @pytest.mark.asyncio
    async def test_query_is_vectorised_before_searching(self):
        target_vector = [0.1, 0.2, 0.3]
        engine = _build_vector_engine(embed_rv=[target_vector])
        with patch(_VEC_ENGINE_PATH, return_value=engine):
            await fine_grained_triplet_search(query="my phrase")

        engine.embedding_engine.embed_text.assert_called_once_with(["my phrase"])
        for invocation in engine.search.call_args_list:
            assert invocation[1]["query_vector"] == target_vector


# ---------------------------------------------------------------------------
# Node-ID extraction & deduplication
# ---------------------------------------------------------------------------


class TestNodeIdExtraction:
    @pytest.mark.asyncio
    async def test_collects_ids_from_global_search(self):
        hits = [
            _HitResult("aaa", 0.95),
            _HitResult("bbb", 0.87),
            _HitResult("ccc", 0.92),
        ]
        engine = _build_vector_engine(search_rv=hits)
        frag = _build_fragment()

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH, return_value=frag) as patched:
                await fine_grained_triplet_search(query="lookup", node_name=None)

        kw = patched.call_args[1]
        assert set(kw["relevant_ids_to_filter"]) == {"aaa", "bbb", "ccc"}

    @pytest.mark.asyncio
    async def test_deduplicates_across_collections(self):
        def _route(*_a, **kw):
            col = kw.get("collection_name")
            if col == "Episode_summary":
                return [_HitResult("x1", 0.95), _HitResult("x2", 0.87)]
            if col == "Entity_name":
                return [_HitResult("x1", 0.90), _HitResult("x3", 0.92)]
            return []

        engine = _build_vector_engine(search_rv=_route)
        frag = _build_fragment()

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH, return_value=frag) as patched:
                await fine_grained_triplet_search(query="lookup", node_name=None)

        ids = patched.call_args[1]["relevant_ids_to_filter"]
        assert set(ids) == {"x1", "x2", "x3"}
        assert len(ids) == 3

    @pytest.mark.asyncio
    async def test_excludes_edge_collection_ids(self):
        def _route(*_a, **kw):
            col = kw.get("collection_name")
            if col == "Entity_name":
                return [_HitResult("n1", 0.95)]
            if col == "RelationType_relationship_name":
                return [_HitResult("e1", 0.88)]
            return []

        engine = _build_vector_engine(search_rv=_route)
        frag = _build_fragment()

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH, return_value=frag) as patched:
                await fine_grained_triplet_search(
                    query="lookup",
                    node_name=None,
                    collections=[
                        "Entity_name",
                        "RelationType_relationship_name",
                    ],
                )

        assert patched.call_args[1]["relevant_ids_to_filter"] == ["n1"]

    @pytest.mark.asyncio
    async def test_skips_results_lacking_id_attribute(self):
        class _NoIdHit:
            def __init__(self, score):
                self.score = score

        def _route(*_a, **kw):
            col = kw.get("collection_name")
            if col == "Entity_name":
                return [
                    _HitResult("p1", 0.95),
                    _NoIdHit(0.90),
                    _HitResult("p2", 0.87),
                ]
            return []

        engine = _build_vector_engine(search_rv=_route)
        frag = _build_fragment()

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH, return_value=frag) as patched:
                await fine_grained_triplet_search(query="lookup", node_name=None)

        assert set(patched.call_args[1]["relevant_ids_to_filter"]) == {"p1", "p2"}

    @pytest.mark.asyncio
    async def test_handles_tuple_shaped_results(self):
        def _route(*_a, **kw):
            col = kw.get("collection_name")
            if col == "Entity_name":
                return (_HitResult("t1", 0.95), _HitResult("t2", 0.87))
            return []

        engine = _build_vector_engine(search_rv=_route)
        frag = _build_fragment()

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH, return_value=frag) as patched:
                await fine_grained_triplet_search(query="lookup", node_name=None)

        assert set(patched.call_args[1]["relevant_ids_to_filter"]) == {"t1", "t2"}

    @pytest.mark.asyncio
    async def test_mixed_empty_and_populated_collections(self):
        def _route(*_a, **kw):
            col = kw.get("collection_name")
            if col == "Episode_summary":
                return [_HitResult("m1", 0.95)]
            if col == "Entity_name":
                return [_HitResult("m2", 0.92)]
            return []

        engine = _build_vector_engine(search_rv=_route)
        frag = _build_fragment()

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH, return_value=frag) as patched:
                await fine_grained_triplet_search(query="lookup", node_name=None)

        assert set(patched.call_args[1]["relevant_ids_to_filter"]) == {"m1", "m2"}


# ---------------------------------------------------------------------------
# Memory-fragment lifecycle
# ---------------------------------------------------------------------------


class TestMemoryFragmentLifecycle:
    @pytest.mark.asyncio
    async def test_reuses_caller_supplied_fragment(self):
        caller_frag = _build_fragment()
        engine = _build_vector_engine(search_rv=[_HitResult("z", 0.95)])

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH) as patched:
                await fine_grained_triplet_search(
                    query="reuse",
                    memory_fragment=caller_frag,
                    node_name=["some"],
                )

        patched.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_fragment_when_absent(self):
        engine = _build_vector_engine(search_rv=[_HitResult("z", 0.95)])
        frag = _build_fragment()

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH, return_value=frag) as patched:
                await fine_grained_triplet_search(query="create", node_name=["some"])

        patched.assert_called_once()

    @pytest.mark.asyncio
    async def test_forwards_top_k_to_importance_calc(self):
        engine = _build_vector_engine(search_rv=[_HitResult("z", 0.95)])
        frag = _build_fragment()
        desired_k = 15

        with patch(_VEC_ENGINE_PATH, return_value=engine):
            with patch(_FRAGMENT_PATH, return_value=frag):
                await fine_grained_triplet_search(query="topk", top_k=desired_k, node_name=["n"])

        frag.calculate_top_triplet_importances.assert_called_once_with(k=desired_k)


# ---------------------------------------------------------------------------
# get_memory_fragment error handling
# ---------------------------------------------------------------------------


class TestGetMemoryFragmentErrors:
    @pytest.mark.asyncio
    async def test_returns_empty_graph_on_concept_not_found(self):
        graph_engine = AsyncMock()
        graph_engine.project_graph_from_db = AsyncMock(side_effect=ConceptNotFoundError("missing concept"))
        with patch(_GRAPH_ENGINE_PATH, return_value=graph_engine):
            result = await get_memory_fragment()

        assert isinstance(result, MemoryGraph)
        assert len(result.nodes) == 0

    @pytest.mark.asyncio
    async def test_returns_empty_graph_on_unexpected_error(self):
        graph_engine = AsyncMock()
        graph_engine.project_graph_from_db = AsyncMock(side_effect=Exception("unexpected failure"))
        with patch(_GRAPH_ENGINE_PATH, return_value=graph_engine):
            result = await get_memory_fragment()

        assert isinstance(result, MemoryGraph)
        assert len(result.nodes) == 0
