"""Unit coverage for `persist_memory_nodes` and its graph/triplet helpers.

These tests mirror the behavioral contract of persisting memory vertices and
their edges: validation, graph engine interaction, indexing order, and
triplet-derived embedding text. Naming and literals are chosen to stay
domain-specific to M-Flow memory nodes rather than generic node wording.
"""

import sys

import pytest
from unittest.mock import AsyncMock, patch

from m_flow.core import MemoryNode
from m_flow.core.domain.models import MemoryTriplet
from m_flow.storage.add_memory_nodes import (
    InvalidMemoryNodesInAddMemoryNodesError,
    _create_triplets_from_graph,
    _extract_embeddable_text_from_datapoint,
    persist_memory_nodes,
)

memory_nodes_under_test = sys.modules["m_flow.storage.add_memory_nodes"]


class StubMemoryVertex(MemoryNode):
    """Minimal concrete memory node with a single indexed text field."""

    text: str
    metadata: dict = {"index_fields": ["text"]}


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_batch", [None, ["not_a_memory_node"]])
async def test_persist_memory_nodes_rejects_invalid_payloads(invalid_batch):
    """`persist_memory_nodes` must raise when the batch is not a list of nodes."""
    with pytest.raises(InvalidMemoryNodesInAddMemoryNodesError):
        await persist_memory_nodes(invalid_batch)


@pytest.mark.asyncio
@patch.object(memory_nodes_under_test, "index_relations")
@patch.object(memory_nodes_under_test, "index_memory_nodes")
@patch.object(memory_nodes_under_test, "get_graph_provider")
@patch.object(memory_nodes_under_test, "deduplicate_nodes_and_edges")
@patch.object(memory_nodes_under_test, "extract_graph")
async def test_persist_memory_nodes_merges_edges_before_single_link_index(
    patch_graph_from_model,
    patch_dedupe,
    patch_engine_factory,
    patch_index_vertices,
    patch_index_links,
):
    """Edges from models plus custom edges are written, then links indexed once."""
    vertex_a = StubMemoryVertex(text="ledger row 7")
    vertex_b = StubMemoryVertex(text="ledger row 42")

    model_edge = (
        str(vertex_a.id),
        str(vertex_b.id),
        "associated_with",
        {"edge_text": "cross_reference"},
    )
    extra_edges = [
        (str(vertex_b.id), str(vertex_a.id), "manual_annotation", {}),
    ]

    patch_graph_from_model.side_effect = [
        ([vertex_a], [model_edge]),
        ([vertex_b], []),
    ]
    patch_dedupe.side_effect = lambda nodes, edges: (nodes, edges)
    async_engine = AsyncMock()
    patch_engine_factory.return_value = async_engine

    outcome = await persist_memory_nodes([vertex_a, vertex_b], custom_edges=extra_edges)

    assert outcome == [vertex_a, vertex_b]
    async_engine.add_nodes.assert_awaited_once()
    patch_index_vertices.assert_awaited_once()
    # Implementation detail: model edges first, then caller-supplied edges; one link index pass after merge.
    assert async_engine.add_edges.await_count == 2
    assert model_edge in async_engine.add_edges.await_args_list[0].args[0]
    assert async_engine.add_edges.await_args_list[1].args[0] == extra_edges
    assert patch_index_links.await_count == 1


@pytest.mark.asyncio
@patch.object(memory_nodes_under_test, "index_relations")
@patch.object(memory_nodes_under_test, "index_memory_nodes")
@patch.object(memory_nodes_under_test, "get_graph_provider")
@patch.object(memory_nodes_under_test, "deduplicate_nodes_and_edges")
@patch.object(memory_nodes_under_test, "extract_graph")
async def test_triplet_embedding_runs_second_index_on_derived_triplets(
    patch_graph_from_model,
    patch_dedupe,
    patch_engine_factory,
    patch_index_vertices,
    patch_index_links,
):
    """With `embed_triplets=True`, the second index call receives `MemoryTriplet` rows."""
    origin = StubMemoryVertex(text="upstream fact")
    sink = StubMemoryVertex(text="downstream inference")

    bridge = (
        str(origin.id),
        str(sink.id),
        "implies",
        {"edge_text": "supports_claim"},
    )

    patch_graph_from_model.side_effect = [
        ([origin], [bridge]),
        ([sink], []),
    ]
    patch_dedupe.side_effect = lambda nodes, edges: (nodes, edges)
    async_engine = AsyncMock()
    patch_engine_factory.return_value = async_engine

    await persist_memory_nodes([origin, sink], embed_triplets=True)

    assert patch_index_vertices.await_count == 2
    first_batch = patch_index_vertices.await_args_list[0].args[0]
    second_batch = patch_index_vertices.await_args_list[1].args[0]
    assert first_batch == [origin, sink]
    assert len(second_batch) == 1
    assert isinstance(second_batch[0], MemoryTriplet)
    patch_index_links.assert_awaited_once()


@pytest.mark.asyncio
@patch.object(memory_nodes_under_test, "index_relations")
@patch.object(memory_nodes_under_test, "index_memory_nodes")
@patch.object(memory_nodes_under_test, "get_graph_provider")
@patch.object(memory_nodes_under_test, "deduplicate_nodes_and_edges")
@patch.object(memory_nodes_under_test, "extract_graph")
async def test_empty_batch_short_circuits_without_graph_extraction(
    patch_graph_from_model,
    patch_dedupe,
    patch_engine_factory,
    patch_index_vertices,
    patch_index_links,
):
    """An empty list still touches the engine with an empty node set and skips per-model graph work."""
    patch_dedupe.side_effect = lambda nodes, edges: (nodes, edges)
    async_engine = AsyncMock()
    patch_engine_factory.return_value = async_engine

    outcome = await persist_memory_nodes([])

    assert outcome == []
    patch_graph_from_model.assert_not_called()
    async_engine.add_nodes.assert_awaited_once_with([])


@pytest.mark.asyncio
@patch.object(memory_nodes_under_test, "index_relations")
@patch.object(memory_nodes_under_test, "index_memory_nodes")
@patch.object(memory_nodes_under_test, "get_graph_provider")
@patch.object(memory_nodes_under_test, "deduplicate_nodes_and_edges")
@patch.object(memory_nodes_under_test, "extract_graph")
async def test_singleton_batch_indexes_once_after_graph_resolution(
    patch_graph_from_model,
    patch_dedupe,
    patch_engine_factory,
    patch_index_vertices,
    patch_index_links,
):
    """One memory node triggers a single `extract_graph` and one vertex index await."""
    lone = StubMemoryVertex(text="orphan snippet 99")
    patch_graph_from_model.side_effect = [([lone], [])]
    patch_dedupe.side_effect = lambda nodes, edges: (nodes, edges)
    async_engine = AsyncMock()
    patch_engine_factory.return_value = async_engine

    outcome = await persist_memory_nodes([lone])

    assert outcome == [lone]
    patch_graph_from_model.assert_called_once()
    patch_index_vertices.assert_awaited_once()


def test_embeddable_concatenation_single_index_field():
    """A node with one `index_fields` entry returns that field verbatim."""
    record = StubMemoryVertex(text="retrieval cue 0x3f")
    assembled = _extract_embeddable_text_from_datapoint(record)
    assert assembled == "retrieval cue 0x3f"


def test_embeddable_concatenation_respects_field_order():
    """Multiple indexed fields are joined with spaces in declaration order."""

    class DualFieldVertex(MemoryNode):
        headline: str
        body: str
        metadata: dict = {"index_fields": ["headline", "body"]}

    record = DualFieldVertex(headline="Quarterly", body="Summary 2024-Q3")
    assembled = _extract_embeddable_text_from_datapoint(record)
    assert assembled == "Quarterly Summary 2024-Q3"


def test_embeddable_text_empty_when_index_fields_absent():
    """Explicitly empty `index_fields` yields an empty embedding string."""

    class ZeroIndexedFields(MemoryNode):
        text: str
        metadata: dict = {"index_fields": []}

    record = ZeroIndexedFields(text="should not surface")
    assembled = _extract_embeddable_text_from_datapoint(record)
    assert assembled == ""


def test_triplet_factory_maps_edge_payload_to_memory_triplet():
    """`_create_triplets_from_graph` builds one `MemoryTriplet` per valid edge."""
    left = StubMemoryVertex(text="entity north")
    right = StubMemoryVertex(text="entity south")
    arc = (str(left.id), str(right.id), "bridges", {"edge_text": "semantic tie"})

    built = _create_triplets_from_graph([left, right], [arc])

    assert len(built) == 1
    assert isinstance(built[0], MemoryTriplet)
    assert built[0].from_node_id == str(left.id)
    assert built[0].to_node_id == str(right.id)
    assert "entity north" in built[0].text
    assert "entity south" in built[0].text


def test_embeddable_text_none_node_yields_empty_string():
    """Passing `None` must not raise and must return empty text."""
    assembled = _extract_embeddable_text_from_datapoint(None)
    assert assembled == ""


def test_embeddable_text_missing_metadata_yields_empty():
    """Nodes without a `metadata` attribute contribute nothing to embeddable text."""

    class MetadataStripped(MemoryNode):
        text: str

    record = MetadataStripped(text="invisible payload")
    delattr(record, "metadata")
    assembled = _extract_embeddable_text_from_datapoint(record)
    assert assembled == ""


def test_embeddable_text_whitespace_only_becomes_empty():
    """Whitespace-only indexed content is treated as empty for embedding."""

    class BlankishText(MemoryNode):
        text: str
        metadata: dict = {"index_fields": ["text"]}

    record = BlankishText(text="   \t  ")
    assembled = _extract_embeddable_text_from_datapoint(record)
    assert assembled == ""


def test_triplet_factory_ignores_truncated_edge_records():
    """Edges shorter than four elements are ignored."""
    solo = StubMemoryVertex(text="island node")
    stub_edge = (str(solo.id), str(solo.id))

    built = _create_triplets_from_graph([solo], [stub_edge])

    assert len(built) == 0


def test_triplet_factory_drops_edges_without_origin_match():
    """If the source id is missing from the vertex list, no triplet is emitted."""
    only_sink = StubMemoryVertex(text="receiver only")
    orphan_in = ("ghost-uuid-0001", str(only_sink.id), "feeds", {})

    built = _create_triplets_from_graph([only_sink], [orphan_in])

    assert len(built) == 0


def test_triplet_factory_drops_edges_without_destination_match():
    """If the target id is missing from the vertex list, no triplet is emitted."""
    only_source = StubMemoryVertex(text="emitter only")
    orphan_out = (str(only_source.id), "ghost-uuid-0002", "feeds", {})

    built = _create_triplets_from_graph([only_source], [orphan_out])

    assert len(built) == 0


def test_triplet_factory_requires_non_null_relation_type():
    """A `None` relationship type must not produce a triplet."""
    head = StubMemoryVertex(text="head cell")
    tail = StubMemoryVertex(text="tail cell")
    bad_arc = (str(head.id), str(tail.id), None, {})

    built = _create_triplets_from_graph([head, tail], [bad_arc])

    assert len(built) == 0


def test_triplet_text_falls_back_to_relation_label():
    """When `edge_text` is absent, the relationship name appears in triplet text."""
    head = StubMemoryVertex(text="prefix token")
    tail = StubMemoryVertex(text="suffix token")
    bare_arc = (str(head.id), str(tail.id), "maps_to", {})

    built = _create_triplets_from_graph([head, tail], [bare_arc])

    assert len(built) == 1
    assert "maps_to" in built[0].text


def test_triplet_factory_collapses_identical_edges():
    """Duplicate edge tuples should yield a single triplet."""
    head = StubMemoryVertex(text="dup a")
    tail = StubMemoryVertex(text="dup b")
    repeated = (str(head.id), str(tail.id), "same_as", {"edge_text": "mirror"})

    built = _create_triplets_from_graph([head, tail], [repeated, repeated])

    assert len(built) == 1


def test_triplet_factory_excludes_vertices_lacking_stable_id():
    """Vertices without `.id` cannot participate as endpoints."""

    class AnonymousVertex:
        pass

    known = StubMemoryVertex(text="known side")
    stranger = AnonymousVertex()
    half_arc = (str(known.id), "opaque-remote-id", "pairs_with", {})

    built = _create_triplets_from_graph([known, stranger], [half_arc])

    assert len(built) == 0


@pytest.mark.asyncio
@patch.object(memory_nodes_under_test, "index_relations")
@patch.object(memory_nodes_under_test, "index_memory_nodes")
@patch.object(memory_nodes_under_test, "get_graph_provider")
@patch.object(memory_nodes_under_test, "deduplicate_nodes_and_edges")
@patch.object(memory_nodes_under_test, "extract_graph")
async def test_explicit_empty_custom_edges_still_schedules_one_edge_write(
    patch_graph_from_model,
    patch_dedupe,
    patch_engine_factory,
    patch_index_vertices,
    patch_index_links,
):
    """`custom_edges=[]` still results in one `add_edges` await (model edges path)."""
    unit = StubMemoryVertex(text="fixture token 512")
    patch_graph_from_model.side_effect = [([unit], [])]
    patch_dedupe.side_effect = lambda nodes, edges: (nodes, edges)
    async_engine = AsyncMock()
    patch_engine_factory.return_value = async_engine

    outcome = await persist_memory_nodes([unit], custom_edges=[])

    assert outcome == [unit]
    assert async_engine.add_edges.await_count == 1
