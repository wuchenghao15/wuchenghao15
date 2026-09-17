"""JSON-backed FAISS index persistence for AutoModel/AutoList (#116).

New dumps are plain JSON (no pickle, safe to load); legacy pickle indexes
from older releases still load with a deserialization warning.
"""

import json
import logging

import pytest
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from pydantic import BaseModel

from hyperextract.types import AutoList, AutoModel
from hyperextract.utils.json_index import (
    dump_index_json,
    has_json_index,
    load_index_json,
)


class _City(BaseModel):
    name: str
    country: str = ""


def _model(llm_client, embedder, tmp_path):
    ka = AutoModel(
        data_schema=_City,
        llm_client=llm_client,
        embedder=embedder,
    )
    # Seed the index directly: page_content is the field name, metadata
    # carries the raw fields — same shape build_index() produces.
    ka._index = FAISS.from_documents(
        [
            Document(page_content="name", metadata={"raw": {"name": "Paris"}}),
            Document(
                page_content="country",
                metadata={"raw": {"name": "Paris", "country": "FR"}},
            ),
        ],
        ka.embedder,
    )
    return ka


def _list(llm_client, embedder):
    return AutoList(
        item_schema=_City,
        llm_client=llm_client,
        embedder=embedder,
    )


def _seed_list(ka):
    ka._index = FAISS.from_documents(
        [
            Document(page_content="name", metadata={"raw": {"name": "Paris"}}),
            Document(page_content="name", metadata={"raw": {"name": "Tokyo"}}),
        ],
        ka.embedder,
    )


class TestJsonRoundTrip:
    def test_dump_writes_json_and_drops_legacy(self, llm_client, embedder, tmp_path):
        ka = _model(llm_client, embedder, tmp_path)
        # Simulate a legacy folder first
        ka._index.save_local(tmp_path)
        assert (tmp_path / "index.faiss").exists()

        ka.dump_index(tmp_path)

        assert has_json_index(tmp_path)
        assert not (tmp_path / "index.faiss").exists()
        assert not (tmp_path / "index.pkl").exists()

    def test_model_round_trip_preserves_search(self, llm_client, embedder, tmp_path):
        ka = _model(llm_client, embedder, tmp_path)
        ka.build_index()
        ka.dump_index(tmp_path)

        restored = _model(llm_client, embedder, tmp_path)
        restored.load_index(tmp_path)
        # Compare at the index level: AutoModel.search() additionally needs
        # extracted data, which this round-trip does not carry.
        original_docs = ka._index.similarity_search("name", k=2)
        restored_docs = restored._index.similarity_search("name", k=2)
        assert [d.metadata for d in restored_docs] == [
            d.metadata for d in original_docs
        ]

    def test_list_round_trip(self, llm_client, embedder, tmp_path):
        ka = _list(llm_client, embedder)
        _seed_list(ka)
        ka.build_index()
        ka.dump_index(tmp_path)

        restored = _list(llm_client, embedder)
        restored.load_index(tmp_path)
        hits = restored.search("Paris", top_k=2)
        assert {h.name for h in hits} <= {"Paris", "Tokyo"}

    def test_json_load_is_picle_free_payload(self, llm_client, embedder, tmp_path):
        ka = _model(llm_client, embedder, tmp_path)
        ka.build_index()
        ka.dump_index(tmp_path)
        payload = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
        assert payload["version"] == 1
        assert payload["dimension"] > 0
        assert len(payload["vectors"]) == len(payload["texts"])


class TestLegacyCompat:
    def test_legacy_pickle_folder_still_loads(
        self, llm_client, embedder, tmp_path, caplog
    ):
        ka = _model(llm_client, embedder, tmp_path)
        ka.build_index()
        # Simulate an old KA: raw save_local, no index.json
        ka._index.save_local(tmp_path)
        assert not has_json_index(tmp_path)

        restored = _model(llm_client, embedder, tmp_path)
        with caplog.at_level(logging.WARNING):
            restored.load_index(tmp_path)

        assert restored._index is not None
        assert any(
            "deserialization" in r.getMessage().lower() for r in caplog.records
        ), "legacy load must warn about deserialization"

    def test_json_preferred_over_legacy(self, llm_client, embedder, tmp_path, caplog):
        ka = _model(llm_client, embedder, tmp_path)
        ka.build_index()
        ka._index.save_local(tmp_path)  # legacy files present...
        ka.dump_index(tmp_path)  # ...but dump removes them and writes JSON

        caplog.clear()
        restored = _model(llm_client, embedder, tmp_path)
        restored.load_index(tmp_path)
        assert not any(
            "deserialization" in r.getMessage().lower() for r in caplog.records
        ), "JSON load must not trigger the legacy deserialization warning"

    def test_missing_folder_raises(self, llm_client, embedder, tmp_path):
        ka = _model(llm_client, embedder, tmp_path)
        with pytest.raises(ValueError, match="does not exist"):
            ka.load_index(tmp_path / "nope")


class TestHelpers:
    def test_load_index_json_returns_none_without_json(self, tmp_path, embedder):
        tmp_path.mkdir(exist_ok=True)
        assert load_index_json(tmp_path, embedder) is None

    def test_corrupt_json_raises(self, tmp_path, embedder):
        (tmp_path / "index.json").write_text('{"version": 1}', encoding="utf-8")
        with pytest.raises(ValueError, match="Corrupt"):
            load_index_json(tmp_path, embedder)

    def test_dump_index_json_round_trip_helper(self, tmp_path, embedder):
        idx = FAISS.from_documents(
            [Document(page_content="f", metadata={"raw": {"k": "v"}})], embedder
        )
        path = dump_index_json(idx, tmp_path)
        assert path.name == "index.json"
        restored = load_index_json(tmp_path, embedder)
        assert restored is not None
        assert restored.index.ntotal == idx.index.ntotal
