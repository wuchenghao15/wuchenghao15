"""AutoSet provenance: recording, scoped search, tags, upsert, persistence.

Before this fix, AutoSet enabled ``track_sources`` on its memory but never
recorded sources during feed — the ledger stayed empty, scoped search
returned nothing, and ``he tag`` / ``he feed --source`` change detection
crashed with AttributeError (no delegation surface at all).

Rollback/scoped-search tests seed the memory directly (like
test_graph_rag.py) so they do not depend on what the mock LLM extracts.
"""

import json

import pytest
from pydantic import BaseModel

from hyperextract.types import AutoSet


class _Item(BaseModel):
    name: str
    category: str = "general"


@pytest.fixture
def ka(llm_client, embedder):
    return AutoSet(
        item_schema=_Item,
        key_extractor=lambda x: x.name,
        llm_client=llm_client,
        embedder=embedder,
    )


def _seed(ka, source_id, name):
    """Attribute one item to a source without going through the LLM."""
    ka._data_memory.add([_Item(name=name)], source_id=source_id)


class TestSourceRecording:
    def test_feed_records_source(self, ka):
        ka.feed_text("Apple and Steve.", source_id="d1", content_hash="h1")
        assert "d1" in ka.sources()
        assert ka.source_content_hash("d1") == "h1"

    def test_scoped_search_returns_attributed_items(self, ka):
        _seed(ka, "d1", "Apple")
        _seed(ka, "d2", "Tesla")
        ka.build_index()

        hits = ka.search("Apple", top_k=5, source_ids=["d1"])
        assert [item.name for item in hits] == ["Apple"]

    def test_scope_on_empty_ledger_is_empty(self, llm_client, embedder):
        # A KA fed WITHOUT --source has no ledger: scoped search must not
        # silently return out-of-scope items.
        other = AutoSet(
            item_schema=_Item,
            key_extractor=lambda x: x.name,
            llm_client=llm_client,
            embedder=embedder,
        )
        other.feed_text("Apple and Steve.")
        other.build_index()
        assert other.search("Apple", top_k=5, source_ids=["d1"]) == []

    def test_chat_forwards_scope_to_search(self, ka):
        from langchain_core.messages import AIMessage
        from langchain_core.runnables import RunnableLambda

        seen = {}

        def _spy(query, top_k=3, **kwargs):
            seen["source_ids"] = kwargs.get("source_ids")
            seen["tags"] = kwargs.get("tags")
            return []

        ka.search = _spy
        ka.llm_client = RunnableLambda(lambda _: AIMessage(content="ok"))
        ka.chat("q", source_ids=["s1"], tags=["t1"])
        assert seen["source_ids"] == ["s1"]
        assert seen["tags"] == ["t1"]


class TestTagsAndRollback:
    def test_tag_round_trip(self, ka):
        _seed(ka, "d1", "Apple")
        assert ka.tag_source("d1", add=["tech"]) == ["tech"]
        assert ka.source_tags("d1") == ["tech"]

    def test_remove_source_keeps_others(self, ka):
        _seed(ka, "d1", "Apple")
        _seed(ka, "d2", "Tesla")
        ka.build_index()

        report = ka.remove_source("d1")
        assert report["removed_items"]
        names = [item.name for item in ka.data.items]
        assert "Apple" not in names and "Tesla" in names

    def test_upsert_replaces_previous_version(self, ka):
        _seed(ka, "d2", "Tesla")
        ka.feed_text("Apple and Steve.", source_id="d1", content_hash="h1")
        ka.feed_text("Rewritten doc one.", source_id="d1", content_hash="h2")

        assert ka.source_content_hash("d1") == "h2"
        # Whatever the extraction produced, the pre-upsert ledger state was
        # rolled back and re-recorded under the same source id.
        assert "d1" in ka.sources()
        assert "d2" in ka.sources()


class TestPersistence:
    def test_ledger_persists_across_dump_load(self, ka, llm_client, embedder, tmp_path):
        _seed(ka, "d1", "Apple")
        _seed(ka, "d2", "Tesla")
        # Feed under a THIRD source — feeding under d1 would (correctly)
        # roll back d1's seeded contributions via upsert semantics.
        ka.feed_text("Some text.", source_id="d3", content_hash="h1")
        ka.build_index()
        ka.dump(tmp_path)

        assert (tmp_path / "sources_items.json").exists()

        restored = AutoSet(
            item_schema=_Item,
            key_extractor=lambda x: x.name,
            llm_client=llm_client,
            embedder=embedder,
        )
        restored.load(tmp_path)
        assert {"d1", "d2", "d3"} <= set(restored.sources())
        assert restored.source_content_hash("d3") == "h1"

        restored.build_index()
        hits = restored.search("Apple", top_k=5, source_ids=["d1"])
        names = [item.name for item in hits]
        assert "Apple" in names and "Tesla" not in names

    def test_data_json_shape_unchanged(self, ka, tmp_path):
        _seed(ka, "d1", "Apple")
        ka.dump(tmp_path)
        data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
        assert isinstance(data["items"], list)
        assert [i["name"] for i in data["items"]] == ["Apple"]
