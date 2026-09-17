"""Integration test: provenance lifecycle against REAL LLM APIs.

Provider-configurable via environment variables (defaults to the
chatanywhere-compatible config in .env):

    HE_TEST_LLM_BASE_URL     LLM endpoint   (default: OPENAI_BASE_URL)
    HE_TEST_LLM_API_KEY      LLM key        (default: OPENAI_API_KEY)
    HE_TEST_LLM_MODEL        LLM model      (default: gpt-4o-mini)
    HE_TEST_EMBED_BASE_URL   embed endpoint (default: LLM base URL)
    HE_TEST_EMBED_API_KEY    embed key      (default: LLM key)
    HE_TEST_EMBED_MODEL      embed model    (default: text-embedding-3-small)

Example — DeepSeek LLM + chatanywhere embeddings:
    HE_TEST_LLM_BASE_URL=https://api.deepseek.com \\
    HE_TEST_LLM_API_KEY=sk-... HE_TEST_LLM_MODEL=deepseek-chat \\
    HE_TEST_EMBED_BASE_URL=https://api.chatanywhere.tech/v1 \\
    HE_TEST_EMBED_API_KEY=sk-... \\
    pytest tests/integration/test_provenance_real.py -v

Exercises the exact-replay question mocks cannot answer: when a document
is rolled back and its keys re-merged from surviving sources, the
LLM.BALANCED merger replays with real non-determinism — we assert
semantic preservation (entity/fact survival), not wording.
"""

import hashlib
import os

import pytest
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel

from hyperextract.types import AutoGraph

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    ),
]


class Entity(BaseModel):
    name: str
    type: str = "organization"
    description: str = ""


class Relation(BaseModel):
    source: str
    target: str
    relation_type: str
    description: str = ""


DOC1_V1 = (
    "Apple was founded by Steve Jobs in 1976. "
    "Google was founded by Larry Page and Sergey Brin in 1998. "
    "Apple is headquartered in Cupertino, California."
)
DOC1_V2 = (
    "Apple was founded by Steve Jobs in 1976. "
    "Tim Cook is the CEO of Apple. "
    "Apple is headquartered in Cupertino, California."
)  # Google fact removed from the document
DOC2 = "Microsoft was founded by Bill Gates and Paul Allen in 1975."


def _client_config(prefix: str, fallback_base: str, fallback_key: str):
    base = os.environ.get(f"{prefix}_BASE_URL", fallback_base)
    key = os.environ.get(f"{prefix}_API_KEY", fallback_key)
    return base, key


def _graph():
    llm_base, llm_key = _client_config(
        "HE_TEST_LLM",
        fallback_base=os.environ.get("OPENAI_BASE_URL", ""),
        fallback_key=os.environ.get("OPENAI_API_KEY", ""),
    )
    emb_base, emb_key = _client_config(
        "HE_TEST_EMBED",
        fallback_base=llm_base,
        fallback_key=llm_key,
    )
    llm_model = os.environ.get("HE_TEST_LLM_MODEL", "gpt-4o-mini")
    emb_model = os.environ.get("HE_TEST_EMBED_MODEL", "text-embedding-3-small")

    llm = ChatOpenAI(
        model=llm_model,
        temperature=0,
        api_key=llm_key,
        base_url=llm_base or None,
    )
    embedder = OpenAIEmbeddings(
        model=emb_model,
        api_key=emb_key,
        base_url=emb_base or None,
    )
    return AutoGraph(
        node_schema=Entity,
        edge_schema=Relation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=llm,
        embedder=embedder,
        extraction_mode="one_stage",
    )


def _names(graph):
    return {n.name for n in graph.nodes}


class TestProvenanceRealAPI:
    def test_full_lifecycle(self):
        g = _graph()

        # 1. Attributed ingestion of doc1 v1 (real extraction)
        g.feed_text(DOC1_V1, source_id="doc1")
        assert "doc1" in g._node_memory._sources
        names_v1 = _names(g)
        assert "Apple" in names_v1
        assert "Google" in names_v1

        # 2. doc2 contributes to the shared "Apple" key
        g.feed_text(DOC2, source_id="doc2")
        assert "Microsoft" in _names(g)

        # 3. doc1 v2 removes the Google fact → auto-upsert rolls back v1:
        #    Google (sole doc1 contribution) is removed; Apple (shared with
        #    doc2) is re-merged from doc2's raw results with real LLM merge.
        g.feed_text(DOC1_V2, source_id="doc1")

        names_after = _names(g)
        assert "Google" not in names_after
        assert "Microsoft" in names_after
        assert "Apple" in names_after

        # 4. Roll back doc2 entirely → Microsoft goes, Apple stays.
        #    (Real extraction also pulls people/years from DOC2 — all of
        #    them are doc2-only contributions, removed together.)
        report = g.remove_source("doc2")
        removed = set(report["removed_nodes"])
        assert "Microsoft" in removed
        assert "Bill Gates" in removed
        names_final = _names(g)
        assert "Microsoft" not in names_final
        assert "Bill Gates" not in names_final
        assert "Paul Allen" not in names_final
        assert "Apple" in names_final

        # 5. Index patched in place throughout, consistent with storage.
        assert g._node_memory.has_index()
        doc_keys = {
            d.metadata["key"] for d in g._node_memory._index.docstore._dict.values()
        }
        storage_keys = {g.node_key_extractor(n) for n in g.nodes}
        assert doc_keys == storage_keys, (
            f"index/storage key mismatch: index_only={doc_keys - storage_keys}, "
            f"storage_only={storage_keys - doc_keys}"
        )

        # 6. Semantic search still works on the patched index.
        nodes, edges = g.search("Tim Cook CEO of Apple", top_k_nodes=3, top_k_edges=2)
        node_names = [n.name for n in nodes]
        assert "Apple" in node_names or "Tim Cook" in node_names

    def test_content_hash_change_detection(self):
        g = _graph()

        h1 = hashlib.sha256(DOC1_V1.encode()).hexdigest()
        g.feed_text(DOC1_V1, source_id="doc1", content_hash=h1)
        assert g.source_content_hash("doc1") == h1

        # Same hash re-feed is a no-op at the API level (CLI enforces skip).
        h2 = hashlib.sha256(b"changed").hexdigest()
        g.feed_text(DOC1_V2, source_id="doc1", content_hash=h2)
        assert g.source_content_hash("doc1") == h2
