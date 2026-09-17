"""Tests for SourceDocumentStore's one-copy-per-source invariant."""

from hyperextract.utils.document_store import SourceDocumentStore


def test_refeed_same_source_different_name_overwrites(tmp_path):
    """Re-feeding a source with a different filename keeps a single current copy."""
    store = SourceDocumentStore(tmp_path)

    store.store_text("doc1", "version one", original_name="a.txt")
    store.store_text("doc1", "version two", original_name="b.txt")

    archived = store.find("doc1")
    assert len(archived) == 1
    assert archived[0].read_text(encoding="utf-8") == "version two"


def test_store_file_overwrites_prior_copy(tmp_path):
    """store_file also drops a prior archive for the same source."""
    store = SourceDocumentStore(tmp_path)
    first = tmp_path / "first.txt"
    first.write_text("one", encoding="utf-8")
    second = tmp_path / "second.txt"
    second.write_text("two", encoding="utf-8")

    store.store_file("doc1", first)
    store.store_file("doc1", second)

    archived = store.find("doc1")
    assert len(archived) == 1
    assert archived[0].read_text(encoding="utf-8") == "two"


def test_distinct_sources_kept_separately(tmp_path):
    """Different source_ids don't clobber each other."""
    store = SourceDocumentStore(tmp_path)
    store.store_text("doc1", "a", original_name="x.txt")
    store.store_text("doc2", "b", original_name="x.txt")

    assert len(store.find("doc1")) == 1
    assert len(store.find("doc2")) == 1
