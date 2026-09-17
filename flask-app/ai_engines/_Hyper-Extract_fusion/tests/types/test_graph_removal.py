"""Hard delete (remove_nodes / remove_edges) and soft delete (edit_*) for
graph-family AutoTypes (issue #84)."""

import pytest
from ontomem.merger import MergeStrategy
from pydantic import BaseModel, Field

from hyperextract.types import (
    AutoGraph,
    AutoHypergraph,
    AutoTemporalGraph,
)
from tests.mocks import MockChatModel, MockEmbeddings


class Entity(BaseModel):
    name: str
    type: str = "ENTITY"
    description: str = ""


class Relation(BaseModel):
    source: str
    target: str
    relation_type: str
    description: str = ""


class HyperRelation(BaseModel):
    participants: list[str] = Field(default_factory=list)
    relation_type: str = "related"


def _graph():
    return AutoGraph(
        node_schema=Entity,
        edge_schema=Relation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
        node_strategy_or_merger=MergeStrategy.MERGE_FIELD,
        edge_strategy_or_merger=MergeStrategy.MERGE_FIELD,
    )


def _hypergraph():
    return AutoHypergraph(
        node_schema=Entity,
        edge_schema=HyperRelation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.relation_type}_{sorted(x.participants)}",
        nodes_in_edge_extractor=lambda x: tuple(x.participants),
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
    )


class TestHardDelete:
    """remove_nodes / remove_edges: key-level deletion with orphan pruning."""

    def test_remove_node_drops_orphan_edges(self):
        g = _graph()
        g._node_memory.add(
            [Entity(name="Apple"), Entity(name="Google"), Entity(name="Meta")]
        )
        g._edge_memory.add(
            [
                Relation(source="Apple", target="Google", relation_type="partner"),
                Relation(source="Meta", target="Google", relation_type="partner"),
            ]
        )

        report = g.remove_nodes("Apple")

        assert report["removed_nodes"] == ["Apple"]
        assert report["not_found_nodes"] == []
        # The Apple-Google edge dangles (Apple gone) and must be pruned;
        # the Meta-Google edge survives.
        assert report["removed_orphan_edges"] == ["Apple-partner-Google"]
        assert {n.name for n in g.nodes} == {"Google", "Meta"}
        assert {e.source for e in g.edges} == {"Meta"}

    def test_remove_missing_node_is_reported_not_raised(self):
        g = _graph()
        report = g.remove_nodes("Nope")
        assert report["removed_nodes"] == []
        assert report["not_found_nodes"] == ["Nope"]

    def test_remove_edges(self):
        g = _graph()
        g._node_memory.add([Entity(name="A"), Entity(name="B"), Entity(name="C")])
        g._edge_memory.add(
            [
                Relation(source="A", target="B", relation_type="r1"),
                Relation(source="B", target="C", relation_type="r2"),
            ]
        )

        report = g.remove_edges("A-r1-B", "missing")

        assert report["removed_edges"] == ["A-r1-B"]
        assert report["not_found_edges"] == ["missing"]
        assert {e.relation_type for e in g.edges} == {"r2"}
        assert {n.name for n in g.nodes} == {"A", "B", "C"}  # nodes untouched

    def test_removal_survives_dump_load_roundtrip(self, tmp_path):
        g = _graph()
        g._node_memory.add([Entity(name="A"), Entity(name="B")])
        g._edge_memory.add([Relation(source="A", target="B", relation_type="r")])
        g.remove_nodes("A")
        g.dump(tmp_path)

        reloaded = _graph()
        reloaded.load(tmp_path)

        assert [n.name for n in reloaded.nodes] == ["B"]
        assert reloaded.edges == []

    def test_hypergraph_remove_node_drops_touching_hyperedges(self):
        h = _hypergraph()
        h._node_memory.add([Entity(name="A"), Entity(name="B"), Entity(name="C")])
        h._edge_memory.add(
            [
                HyperRelation(participants=["A", "B"], relation_type="group"),
                HyperRelation(participants=["C"], relation_type="solo"),
            ]
        )

        report = h.remove_nodes("A")

        assert report["removed_nodes"] == ["A"]
        keys_removed = report["removed_orphan_edges"]
        assert len(keys_removed) == 1 and "group_" in keys_removed[0]
        assert {e.relation_type for e in h.edges} == {"solo"}

    def test_spatiotemporal_subclass_inherits_removal(self):
        from hyperextract.types import AutoTemporalGraph

        g = AutoTemporalGraph(
            node_schema=Entity,
            edge_schema=Relation,
            node_key_extractor=lambda x: x.name,
            edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
            time_in_edge_extractor=lambda x: "",
            nodes_in_edge_extractor=lambda x: (x.source, x.target),
            llm_client=MockChatModel(),
            embedder=MockEmbeddings(),
        )
        g._node_memory.add([Entity(name="A"), Entity(name="B")])

        report = g.remove_nodes("A", "B", "C")
        assert report["removed_nodes"] == ["A", "B"]
        assert report["not_found_nodes"] == ["C"]


class FakeChatModel:
    """Chat-model stub: with_structured_output returns the canned item.

    Instances are assigned to ``memory.llm_client`` so OMem.edit renders the
    edit prompt and the stub records the rendered text for assertions.
    """

    def __init__(self, canned):
        self.canned = canned  # item returned from the structured rewrite
        self.seen_text: list[str] = []

    def with_structured_output(self, schema):
        model = self

        from langchain_core.runnables import Runnable

        class _Runnable(Runnable):
            def invoke(self, prompt_value, config=None, **kwargs):
                text = str(prompt_value)
                model.seen_text.append(text)
                return model.canned

        return _Runnable()


class _FakeGraphExtractor:
    """One-stage extractor stub returning a canned graph."""

    def __init__(self, result):
        self.result = result

    def invoke(self, input, config=None):
        return self.result

    def batch(self, inputs, config=None, return_exceptions=False, **kwargs):
        return [self.result for _ in inputs]


class TestAutoUpsert:
    """Re-feeding the same source_id replaces that document's version
    (facts removed from the new version do not linger)."""

    def test_second_feed_rolls_back_v1_contributions(self):
        g = _graph()
        v1 = g.graph_schema(
            nodes=[
                Entity(name="A", description="fact v1"),
                Entity(name="B", description="only in v1"),
            ],
            edges=[],
        )
        g.data_extractor = _FakeGraphExtractor(v1)
        g.feed_text("v1 text", source_id="doc-1")
        assert {n.name for n in g.nodes} == {"A", "B"}

        v2 = g.graph_schema(nodes=[Entity(name="A", description="fact v2")], edges=[])
        g.data_extractor = _FakeGraphExtractor(v2)
        g.feed_text("v2 text", source_id="doc-1")

        # B existed only in v1 → rolled back; A carries the v2 fact.
        assert {n.name for n in g.nodes} == {"A"}
        a = next(n for n in g.nodes if n.name == "A")
        assert a.description == "fact v2"

    def test_ledger_keeps_only_current_version(self):
        g = _graph()
        v1 = g.graph_schema(nodes=[Entity(name="A", description="v1")], edges=[])
        g.data_extractor = _FakeGraphExtractor(v1)
        g.feed_text("v1 text", source_id="doc-1")
        assert len(g._node_memory._sources["doc-1"].raw_items) == 1

        v2 = g.graph_schema(nodes=[Entity(name="A", description="v2")], edges=[])
        g.data_extractor = _FakeGraphExtractor(v2)
        g.feed_text("v2 text", source_id="doc-1")

        raws = g._node_memory._sources["doc-1"].raw_items
        assert len(raws) == 1
        assert raws[0]["description"] == "v2"

    def test_feed_without_source_does_not_rollback(self):
        g = _graph()
        v1 = g.graph_schema(
            nodes=[
                Entity(name="A", description="v1"),
                Entity(name="B", description="B"),
            ],
            edges=[],
        )
        g.data_extractor = _FakeGraphExtractor(v1)
        g.feed_text("v1 text", source_id="doc-1")

        # v2 fed WITHOUT a source: no rollback — B stays.
        v2 = g.graph_schema(nodes=[Entity(name="A", description="v2")], edges=[])
        g.data_extractor = _FakeGraphExtractor(v2)
        g.feed_text("v2 text")

        assert {n.name for n in g.nodes} == {"A", "B"}


class TestSpatiotemporalProvenance:
    """Temporal/spatial subclasses participate in source provenance."""

    def _temporal(self):
        return AutoTemporalGraph(
            node_schema=Entity,
            edge_schema=Relation,
            node_key_extractor=lambda x: x.name,
            edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
            time_in_edge_extractor=lambda x: "",
            nodes_in_edge_extractor=lambda x: (x.source, x.target),
            llm_client=MockChatModel(),
            embedder=MockEmbeddings(),
            observation_time="2026-09-05",
            extraction_mode="one_stage",
            chunk_size=100_000,
        )

    def test_temporal_feed_records_and_rolls_back(self):
        g = self._temporal()
        g.data_extractor = _FakeGraphExtractor(
            g.graph_schema(
                nodes=[Entity(name="T1")],
                edges=[Relation(source="T1", target="T1", relation_type="self")],
            )
        )
        g.feed_text("temporal doc", source_id="doc-1")
        assert "doc-1" in g._node_memory._sources
        assert "doc-1" in g._edge_memory._sources

        report = g.remove_source("doc-1")
        assert set(report["removed_nodes"]) == {"T1"}
        assert g.empty()


class TestIndexPatching:
    """Phase A (#84): removals/edits patch the FAISS index in place.

    Assertions inspect the FAISS docstore directly (keys + re-embedded
    page_content) — MockEmbeddings is hash-based, so semantic-search
    result ordering is not meaningful here.
    """

    @staticmethod
    def _docstore(memory):
        return memory._index.docstore._dict

    def test_remove_node_keeps_index_without_stale_vectors(self):
        g = _graph()
        g._node_memory.add(
            [Entity(name="Apple"), Entity(name="Google"), Entity(name="Meta")]
        )
        g._edge_memory.add(
            [Relation(source="Apple", target="Google", relation_type="partner")]
        )
        g.build_index()
        assert g._node_memory.has_index()

        report = g.remove_nodes("Apple")

        assert report["index_patched"] is True
        # Index must survive the removal (no full-rebuild fallback).
        assert g._node_memory.has_index()
        assert g._edge_memory.has_index()
        # The removed node's vector and its edge's vector are gone.
        node_keys = {d.metadata["key"] for d in self._docstore(g._node_memory).values()}
        edge_keys = {d.metadata["key"] for d in self._docstore(g._edge_memory).values()}
        assert node_keys == {"Google", "Meta"}
        assert edge_keys == set()

    def test_remove_node_docstore_shrinks(self):
        g = _graph()
        g._node_memory.add([Entity(name="A"), Entity(name="B")])
        g.build_index()
        size_before = len(g._node_memory._index.docstore._dict)

        g.remove_nodes("A")

        size_after = len(g._node_memory._index.docstore._dict)
        assert size_after == size_before - 1

    def test_edit_node_refreshes_vector(self):
        g = _graph()
        g._node_memory.add(
            [Entity(name="A", description="A was founded by X. A is in Y.")]
        )
        g.build_index()
        g._node_memory.llm_client = FakeChatModel(
            Entity(name="A", description="A is in Y.")
        )

        report = g.edit_node("A", remove_fact="founded by X")

        assert report["index_patched"] is True
        assert g._node_memory.has_index()
        # Exactly one vector for the key, re-embedded with the new text.
        docs = [
            d
            for d in self._docstore(g._node_memory).values()
            if d.metadata["key"] == "A"
        ]
        assert len(docs) == 1
        assert "founded by X" not in docs[0].page_content
        assert "A is in Y" in docs[0].page_content

    def test_no_index_built_falls_back_to_lazy_rebuild(self):
        g = _graph()
        g._node_memory.add([Entity(name="A"), Entity(name="B")])
        # No build_index() call — nothing to patch.

        report = g.remove_nodes("A")

        assert report["index_patched"] is False
        assert not g._node_memory.has_index()
        # OMem's lazy rebuild still reflects the removal.
        assert "A" not in {n.name for n in g.nodes}

    def test_patched_index_survives_dump_load(self, tmp_path):
        g = _graph()
        g._node_memory.add([Entity(name="A"), Entity(name="B")])
        g._edge_memory.add([Relation(source="A", target="B", relation_type="r")])
        g.build_index()
        g.remove_nodes("A")
        g.dump(tmp_path)

        reloaded = _graph()
        reloaded.load(tmp_path)
        assert reloaded._node_memory.has_index()

        node_keys = {
            d.metadata["key"] for d in self._docstore(reloaded._node_memory).values()
        }
        assert node_keys == {"B"}
        edge_keys = {
            d.metadata["key"] for d in self._docstore(reloaded._edge_memory).values()
        }
        assert edge_keys == set()

    def test_hypergraph_removal_patches_index(self):
        h = _hypergraph()
        h._node_memory.add([Entity(name="A"), Entity(name="B"), Entity(name="C")])
        h._edge_memory.add(
            [HyperRelation(participants=["A", "B"], relation_type="group")]
        )
        h.build_index()

        report = h.remove_nodes("A")

        assert report["index_patched"] is True
        assert h._node_memory.has_index()
        node_keys = {d.metadata["key"] for d in self._docstore(h._node_memory).values()}
        assert node_keys == {"B", "C"}
        # The hyperedge containing the removed node is gone from the index.
        edge_keys = {d.metadata["key"] for d in self._docstore(h._edge_memory).values()}
        assert edge_keys == set()


class TestSoftDelete:
    """edit_node / edit_edge: LLM-assisted fact removal with guardrails."""

    def test_edit_dry_run_does_not_apply(self):
        g = _graph()
        g._node_memory.add(
            [Entity(name="A", description="A was founded by X. A is in Y.")]
        )
        g._node_memory.llm_client = FakeChatModel(
            Entity(name="A", description="A is in Y.")
        )

        report = g.edit_node("A", remove_fact="founded by X", dry_run=True)

        assert report["changed"] is True
        assert report["applied"] is False
        # stored item untouched
        assert "founded by X" in g._node_memory.get("A").description

    def test_edit_applies_rewrite(self):
        g = _graph()
        g._node_memory.add(
            [Entity(name="A", description="A was founded by X. A is in Y.")]
        )
        g._node_memory.llm_client = FakeChatModel(
            Entity(name="A", description="A is in Y.")
        )

        report = g.edit_node("A", remove_fact="founded by X")

        assert report["changed"] is True
        assert report["applied"] is True
        assert g._node_memory.get("A").description == "A is in Y."

    def test_editor_receives_item_json_key_and_target(self):
        g = _graph()
        g._node_memory.add([Entity(name="A", description="hello")])
        editor = FakeChatModel(Entity(name="A", description="hello"))
        g._node_memory.llm_client = editor

        g.edit_node("A", instruction="drop everything about X")

        # The rendered edit prompt carries the item JSON, key, and target.
        assert len(editor.seen_text) == 1
        prompt_text = editor.seen_text[0]
        assert '"A"' in prompt_text
        assert "hello" in prompt_text
        assert "drop everything about X" in prompt_text

    def test_key_change_is_rejected(self):
        g = _graph()
        g._node_memory.add([Entity(name="A")])
        g._node_memory.llm_client = FakeChatModel(
            Entity(name="Renamed")
        )  # identity break

        with pytest.raises(ValueError, match="key changed"):
            g.edit_node("A", remove_fact="whatever")
        # nothing was mutated
        assert g._node_memory.get("A").name == "A"

    def test_unchanged_rewrite_reports_no_change(self):
        g = _graph()
        g._node_memory.add([Entity(name="A", description="same")])
        g._node_memory.llm_client = FakeChatModel(Entity(name="A", description="same"))

        report = g.edit_node("A", remove_fact="not present anyway")

        assert report["changed"] is False
        assert g._node_memory.get("A").description == "same"

    def test_missing_key_raises(self):
        g = _graph()
        with pytest.raises(KeyError):
            g.edit_node("Nope", remove_fact="x")

    def test_remove_fact_and_instruction_are_exclusive(self):
        g = _graph()
        with pytest.raises(ValueError, match="exactly one"):
            g.edit_node("A", remove_fact="a", instruction="b")
        with pytest.raises(ValueError, match="exactly one"):
            g.edit_node("A")

    def test_edit_edge(self):
        g = _graph()
        g._node_memory.add([Entity(name="A"), Entity(name="B")])
        g._edge_memory.add(
            [
                Relation(
                    source="A",
                    target="B",
                    relation_type="acquired",
                    description="Acquired by Apple in 2016, first announced in March.",
                )
            ]
        )
        # relation_type is part of the edge key, so the rewrite keeps it and
        # only changes the description — a key-changing rewrite is rejected.
        g._edge_memory.llm_client = FakeChatModel(
            Relation(
                source="A",
                target="B",
                relation_type="acquired",
                description="Acquired by Apple in 2016.",
            )
        )

        report = g.edit_edge("A-acquired-B", remove_fact="first announced in March")

        assert report["applied"] is True
        assert "announced in March" not in g.edges[0].description

    def test_edit_edge_key_change_is_rejected(self):
        g = _graph()
        g._node_memory.add([Entity(name="A"), Entity(name="B")])
        g._edge_memory.add([Relation(source="A", target="B", relation_type="r")])
        g._edge_memory.llm_client = FakeChatModel(
            Relation(source="A", target="B", relation_type="partner")
        )

        with pytest.raises(ValueError, match="key changed"):
            g.edit_edge("A-r-B", remove_fact="whatever")
