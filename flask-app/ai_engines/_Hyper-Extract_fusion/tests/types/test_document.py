"""Tests for AutoDocument (chunk-based corpus, zero extraction cost)."""

import json

import pytest

from hyperextract.types.document import (
    AutoDocument,
    TextChunk,
    chunk_key_extractor,
)


@pytest.fixture
def ka(llm_client, embedder):
    return AutoDocument(llm_client=llm_client, embedder=embedder)


LONG_TEXT = "Alpha loves beta. " * 200  # > default chunk_size -> 2+ chunks
DOC_B = "Gamma is a different document entirely."


class TestIngestion:
    def test_short_text_single_chunk(self, ka):
        ka.feed_text("short text", source_id="doc")
        assert len(ka.data.chunks) == 1
        assert ka.data.chunks[0].content == "short text"

    def test_long_text_chunked_without_llm(self, ka):
        ka.feed_text(LONG_TEXT, source_id="doc")
        assert len(ka.data.chunks) >= 2
        assert all(c.content for c in ka.data.chunks)

    def test_empty_flag(self, ka):
        assert ka.empty()
        ka.feed_text("x", source_id="doc")
        assert not ka.empty()

    def test_sources_recorded_with_hash(self, ka):
        ka.feed_text(LONG_TEXT, source_id="doc", content_hash="abc123")
        assert "doc" in ka.sources()
        assert ka.source_content_hash("doc") == "abc123"

    def test_cross_document_dedup_by_content(self, ka):
        shared = "identical chunk content fed from two documents."
        ka.feed_text(shared, source_id="a")
        ka.feed_text(shared, source_id="b")
        assert len(ka.data.chunks) == 1


class TestSearch:
    def test_search_requires_index(self, ka):
        ka.feed_text("some text", source_id="doc")
        with pytest.raises(ValueError, match="build_index"):
            ka.search("text")

    def test_search_returns_chunks(self, ka):
        ka.feed_text(LONG_TEXT, source_id="docA")
        ka.feed_text(DOC_B, source_id="docB")
        ka.build_index()
        assert ka.has_index()
        results = ka.search("gamma different document", top_k=1)
        assert len(results) == 1
        assert isinstance(results[0], TextChunk)

    def test_scoped_search_by_source(self, ka):
        ka.feed_text(LONG_TEXT, source_id="docA")
        ka.feed_text(DOC_B, source_id="docB")
        ka.build_index()
        results = ka.search("gamma", top_k=5, source_ids=["docB"])
        assert len(results) == 1
        assert "Gamma" in results[0].content

    def test_scoped_search_by_tag(self, ka):
        ka.feed_text(LONG_TEXT, source_id="docA")
        ka.feed_text(DOC_B, source_id="docB")
        ka.tag_source("docB", add=["kb2"])
        ka.build_index()
        assert ka.source_tags("docB") == ["kb2"]
        results = ka.search("gamma", top_k=5, tags=["kb2"])
        assert len(results) == 1
        # The untagged source is excluded from the same query.
        assert all("Alpha" not in c.content for c in results)

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


class TestUpsertAndRollback:
    def test_upsert_replaces_old_chunks(self, ka):
        ka.feed_text(LONG_TEXT, source_id="docA")
        ka.feed_text(DOC_B, source_id="docB")
        ka.feed_text("rewritten docA content", source_id="docA", content_hash="h2")

        contents = [c.content for c in ka.data.chunks]
        assert not any("Alpha" in c for c in contents)
        assert any("rewritten docA" in c for c in contents)
        assert any("Gamma" in c for c in contents)

    def test_remove_source_keeps_others(self, ka):
        ka.feed_text(LONG_TEXT, source_id="docA")
        ka.feed_text(DOC_B, source_id="docB")
        ka.build_index()

        report = ka.remove_source("docA")
        assert report["source_id"] == "docA"
        assert report["removed_chunks"]
        assert not any("Alpha" in c.content for c in ka.data.chunks)
        assert any("Gamma" in c.content for c in ka.data.chunks)

    def test_remove_shared_chunk_remerges_from_survivor(self, ka):
        shared = "shared sentence kept by two documents."
        ka.feed_text(shared, source_id="a")
        ka.feed_text(shared, source_id="b")
        ka.remove_source("a")
        assert [c.content for c in ka.data.chunks] == [shared]


class TestSerialization:
    def test_dump_load_round_trip(self, ka, llm_client, embedder, tmp_path):
        ka.feed_text(LONG_TEXT, source_id="docA", content_hash="ha")
        ka.feed_text(DOC_B, source_id="docB", content_hash="hb")
        ka.build_index()

        ka.dump(tmp_path)
        assert (tmp_path / "data.json").exists()
        assert (tmp_path / "sources_chunks.json").exists()
        data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
        assert {c["content"] for c in data["chunks"]} >= {DOC_B}

        restored = AutoDocument(llm_client=llm_client, embedder=embedder)
        restored.load(tmp_path)
        assert len(restored.data.chunks) == len(ka.data.chunks)
        assert set(restored.sources()) == {"docA", "docB"}
        assert restored.source_content_hash("docA") == "ha"

        restored.build_index()
        hits = restored.search("gamma", top_k=5, source_ids=["docB"])
        assert len(hits) == 1

    def test_parse_returns_new_instance_with_ledger(self, ka):
        parsed = ka.parse(LONG_TEXT, source_id="docA")
        assert parsed is not ka
        assert "docA" in parsed.sources()
        assert parsed.source_content_hash("docA") is None


class TestChunkKeys:
    def test_key_is_stable_and_content_based(self):
        a, b = TextChunk(content="same"), TextChunk(content="same")
        c = TextChunk(content="different")
        assert (
            chunk_key_extractor(a) == chunk_key_extractor(b) != chunk_key_extractor(c)
        )


def test_registry_exports():
    from hyperextract.types import AutoDocument as ExportedAutoDocument

    assert ExportedAutoDocument is AutoDocument
