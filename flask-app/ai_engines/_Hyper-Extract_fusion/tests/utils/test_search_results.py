"""Unit tests for SearchHits / coerce_search_results."""

from pydantic import BaseModel

from hyperextract.utils.search_results import SearchHits, coerce_search_results


class _Node(BaseModel):
    name: str


class _Edge(BaseModel):
    source: str
    target: str


class _Theme(BaseModel):
    title: str


def test_list_wraps_results_and_counts_items():
    hits = coerce_search_results([_Node(name="Alice"), _Node(name="Bob")])
    assert hits.kind == "list"
    assert hits.count == 2
    assert hits.payload == {
        "results": [{"name": "Alice"}, {"name": "Bob"}],
    }


def test_pair_tuple_count_is_nodes_plus_edges_not_arity():
    hits = coerce_search_results(
        ([_Node(name="Alice")], [_Edge(source="Alice", target="Bob")])
    )
    assert hits.kind == "graph"
    assert hits.count == 2
    assert hits.payload["nodes"] == [{"name": "Alice"}]
    assert hits.payload["edges"] == [{"source": "Alice", "target": "Bob"}]
    assert "community_context" not in hits.payload


def test_empty_pair_tuple_has_zero_count():
    hits = coerce_search_results(([], []))
    assert isinstance(hits, SearchHits)
    assert hits.kind == "graph"
    assert hits.count == 0
    assert hits.payload == {"nodes": [], "edges": []}


def test_triple_includes_null_community_context():
    hits = coerce_search_results(([], [], None))
    assert hits.kind == "graph"
    assert hits.count == 0
    assert hits.payload["community_context"] is None


def test_triple_dumps_community_dict():
    hits = coerce_search_results(
        ([_Node(name="Alice")], [], {"summary": "cluster"})
    )
    assert hits.count == 1
    assert hits.payload["community_context"] == {"summary": "cluster"}


def test_mapping_recursively_dumps_models():
    hits = coerce_search_results(
        {
            "themes": [_Theme(title="power")],
            "entities": [_Node(name="Tesla")],
            "nested": {"inner": [_Node(name="nested")]},
        }
    )
    assert hits.kind == "mapping"
    assert hits.count == 3
    assert hits.payload["themes"] == [{"title": "power"}]
    assert hits.payload["entities"] == [{"name": "Tesla"}]
    assert hits.payload["nested"] == {"inner": [{"name": "nested"}]}
