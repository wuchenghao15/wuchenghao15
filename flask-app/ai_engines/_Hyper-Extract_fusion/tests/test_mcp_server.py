"""Tests for the MCP server (hyperextract.mcp_server).

The tool functions are tested directly. The FastMCP wiring is smoke-tested and
skipped if the optional `mcp` package is not installed. The `mcp` package is not
required to import the module or test the tool logic.
"""

import json

import pytest
from pydantic import BaseModel, Field

from hyperextract import mcp_server
from hyperextract.types import AutoGraph
from tests.mocks import MockChatModel, MockEmbeddings


class Entity(BaseModel):
    name: str
    type: str = "ENTITY"
    properties: dict = Field(default_factory=dict)


class Relation(BaseModel):
    source: str
    target: str
    relation_type: str


def _graph_with_index():
    g = AutoGraph(
        node_schema=Entity,
        edge_schema=Relation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
    )
    g._node_memory.add([Entity(name="Apple", type="ORG"), Entity(name="Steve Jobs")])
    g._edge_memory.add(
        [Relation(source="Apple", target="Steve Jobs", relation_type="founded_by")]
    )
    g.build_index()
    g.metadata["template"] = "general/base_graph"
    g.metadata["lang"] = "en"
    return g


# ---------------------------------------------------------------------------
# list_templates
# ---------------------------------------------------------------------------


def test_list_templates_returns_json():
    out = json.loads(mcp_server.list_templates())
    assert isinstance(out, list)
    assert len(out) > 0
    assert {"name", "type", "description"} <= set(out[0].keys())


def test_list_templates_includes_methods_by_default():
    out = json.loads(mcp_server.list_templates())
    names = {item["name"] for item in out}
    assert any(name.startswith("method/") for name in names)
    assert "method/graph_rag" in names or "method/chunk_rag" in names


def test_list_templates_can_hide_methods():
    out = json.loads(mcp_server.list_templates(include_methods=False))
    names = {item["name"] for item in out}
    assert all(not name.startswith("method/") for name in names)


# ---------------------------------------------------------------------------
# info (no client needed — reads json directly)
# ---------------------------------------------------------------------------


def test_info_reports_counts(tmp_path):
    g = _graph_with_index()
    ka = tmp_path / "ka"
    g.dump(ka)

    out = json.loads(mcp_server.info(str(ka)))
    assert out["nodes"] == 2
    assert out["edges"] == 1
    assert out["index_built"] is True
    assert out["template"] == "general/base_graph"
    assert "created" in out
    assert "updated" in out
    assert "sources" not in out


def test_info_includes_chunks_and_optional_sources(tmp_path):
    ka = tmp_path / "doc_ka"
    ka.mkdir()
    (ka / "data.json").write_text(
        json.dumps({"chunks": [{"content": "a"}, {"content": "b"}]}),
        encoding="utf-8",
    )
    (ka / "metadata.json").write_text(
        json.dumps(
            {
                "template": "general/base_document",
                "lang": "en",
                "created_at": "2026-09-12T00:00:00",
                "updated_at": "2026-09-12T01:00:00",
            }
        ),
        encoding="utf-8",
    )
    (ka / "sources_chunks.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "doc-1",
                    "content_hash": "abc",
                    "raw_items": [{"content": "a"}, {"content": "b"}],
                }
            ]
        ),
        encoding="utf-8",
    )

    out = json.loads(mcp_server.info(str(ka)))
    assert out["chunks"] == 2
    assert out["created"] == "2026-09-12T00:00:00"
    assert out["updated"] == "2026-09-12T01:00:00"
    assert "sources" not in out

    with_sources = json.loads(mcp_server.info(str(ka), include_sources=True))
    assert with_sources["sources"] == [
        {"source_id": "doc-1", "raw_items": 2, "content_hash": "abc"}
    ]


def test_info_rejects_non_ka(tmp_path):
    out = mcp_server.info(str(tmp_path / "nope"))
    assert "Not a knowledge abstract" in out


# ---------------------------------------------------------------------------
# search / ask / export — _load_ka monkeypatched to skip the Template reload
# ---------------------------------------------------------------------------


def test_search_returns_nodes_and_edges(monkeypatch):
    g = _graph_with_index()
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)

    out = json.loads(mcp_server.search("x", "technology company", top_k=2))
    assert "nodes" in out and "edges" in out
    assert isinstance(out["nodes"], list)


def test_search_graph_rag_triple_includes_community_context(monkeypatch):
    class _TripleKA:
        def search(self, query, top_k=5):
            return (
                [Entity(name="Alice")],
                [Relation(source="Alice", target="Bob", relation_type="knows")],
                {"summary": "cluster"},
            )

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _TripleKA())
    out = json.loads(mcp_server.search("x", "query"))
    assert "nodes" in out and "edges" in out
    assert out["community_context"] == {"summary": "cluster"}
    assert out["nodes"][0]["name"] == "Alice"


def test_search_graph_rag_triple_writes_null_community(monkeypatch):
    class _TripleKA:
        def search(self, query, top_k=5):
            return ([], [], None)

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _TripleKA())
    out = json.loads(mcp_server.search("x", "query"))
    assert out["nodes"] == []
    assert out["edges"] == []
    assert out["community_context"] is None


def test_search_list_wraps_results(monkeypatch):
    class _ListKA:
        def search(self, query, top_k=5):
            return [Entity(name="Alice"), Entity(name="Bob")]

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _ListKA())
    out = json.loads(mcp_server.search("x", "query"))
    assert "results" in out
    assert [item["name"] for item in out["results"]] == ["Alice", "Bob"]


def test_search_dict_recursively_dumps_models(monkeypatch):
    class _DictKA:
        def search(self, query, top_k=5):
            return {
                "themes": [Entity(name="power")],
                "entities": [Entity(name="Tesla")],
                "nested": {"inner": [Entity(name="nested")]},
            }

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _DictKA())
    out = json.loads(mcp_server.search("x", "query"))
    assert out["themes"][0]["name"] == "power"
    assert out["entities"][0]["name"] == "Tesla"
    assert out["nested"]["inner"][0]["name"] == "nested"


def test_search_without_index_is_handled(monkeypatch):
    g = AutoGraph(
        node_schema=Entity,
        edge_schema=Relation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
    )
    g._node_memory.add([Entity(name="Apple")])
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)

    out = mcp_server.search("x", "anything")
    assert "Cannot search" in out
    assert "build-index" in out


class _StubKA:
    """Stub KA to test the MCP tool wiring independently of chat/export internals
    (those are covered by their own modules; this isolates the MCP layer)."""

    def chat(self, question, top_k=5):
        return type(
            "Resp", (), {"content": f"answer to: {question}", "additional_kwargs": {}}
        )()

    def export_obsidian(self, output, vault_name="", overwrite=False):
        from pathlib import Path

        out = Path(output)
        out.mkdir(parents=True, exist_ok=True)
        (out / "Note.md").write_text("x", encoding="utf-8")
        return out


def test_ask_returns_answer(monkeypatch):
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _StubKA())
    out = mcp_server.ask("x", "Who founded Apple?", top_k=2)
    assert out == "answer to: Who founded Apple?"


def test_export_obsidian(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _StubKA())
    vault = tmp_path / "vault"
    out = mcp_server.export_obsidian("x", str(vault), vault_name="KB", overwrite=True)
    assert "Exported 1 notes" in out
    assert (vault / "Note.md").exists()


def test_export_graphml(monkeypatch, tmp_path):
    g = _graph_with_index()
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)
    dest = tmp_path / "out.graphml"
    out = mcp_server.export_graphml("x", str(dest))
    assert dest.exists()
    xml = dest.read_text(encoding="utf-8")
    assert "<edge" in xml
    assert str(dest) in out


def test_export_graphml_requires_overwrite(monkeypatch, tmp_path):
    g = _graph_with_index()
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)
    dest = tmp_path / "out.graphml"
    dest.write_text("KEEP-ME", encoding="utf-8")
    out = mcp_server.export_graphml("x", str(dest))
    assert "overwrite" in out.lower()
    assert dest.read_text(encoding="utf-8") == "KEEP-ME"
    out = mcp_server.export_graphml("x", str(dest), overwrite=True)
    assert dest.read_text(encoding="utf-8") != "KEEP-ME"
    assert str(dest) in out


def test_export_csv(monkeypatch, tmp_path):
    g = _graph_with_index()
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)
    dest = tmp_path / "csv_out"
    out = mcp_server.export_csv("x", str(dest))
    assert (dest / "nodes.csv").exists()
    assert (dest / "edges.csv").exists()
    assert "nodes.csv + edges.csv" in out


def test_export_graphml_rejects_non_graph(monkeypatch, tmp_path):
    class _ListKA:
        pass

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _ListKA())
    out = mcp_server.export_graphml("x", str(tmp_path / "out.graphml"))
    assert out == (
        "Graph export (GraphML/CSV/JSON-LD/Cypher) is only supported for graph-type "
        "knowledge abstracts (graph, hypergraph, temporal/spatial graphs)."
    )


def test_export_csv_rejects_non_graph_with_same_message(monkeypatch, tmp_path):
    class _ListKA:
        pass

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _ListKA())
    graphml = mcp_server.export_graphml("x", str(tmp_path / "out.graphml"))
    csv_out = mcp_server.export_csv("x", str(tmp_path / "csv"))
    assert graphml == csv_out
    assert "graph-type knowledge abstracts" in graphml


def test_export_cypher(monkeypatch, tmp_path):
    g = _graph_with_index()
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)
    dest = tmp_path / "out.cypher"
    out = mcp_server.export_cypher("x", str(dest))
    assert dest.exists()
    text = dest.read_text(encoding="utf-8")
    assert "MERGE" in text
    assert str(dest) in out


class _HyperedgeEvent(BaseModel):
    label: str
    participants: list[str]


def test_export_cypher_nary_is_hyperedge_not_clique(monkeypatch, tmp_path):
    class _HyperKA:
        nodes = [
            Entity(name="A"),
            Entity(name="B"),
            Entity(name="C"),
        ]
        edges = [_HyperedgeEvent(label="meeting", participants=["C", "A", "B"])]
        node_key_extractor = staticmethod(lambda n: n.name)
        edge_key_extractor = staticmethod(lambda e: e.label)
        nodes_in_edge_extractor = staticmethod(lambda e: tuple(e.participants))

        def export_obsidian(self, *args, **kwargs):
            return None

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _HyperKA())
    dest = tmp_path / "out.cypher"
    out = mcp_server.export_cypher("x", str(dest))
    text = dest.read_text(encoding="utf-8")
    assert ":Hyperedge" in text
    assert "[:IN]" in text
    assert text.count("[:IN]") == 3
    assert "-[:REL]" not in text
    assert str(dest) in out


def test_export_cypher_requires_overwrite(monkeypatch, tmp_path):
    g = _graph_with_index()
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)
    dest = tmp_path / "out.cypher"
    dest.write_text("KEEP-ME", encoding="utf-8")
    out = mcp_server.export_cypher("x", str(dest))
    assert "overwrite" in out.lower()
    assert dest.read_text(encoding="utf-8") == "KEEP-ME"
    out = mcp_server.export_cypher("x", str(dest), overwrite=True)


def test_export_jsonld(monkeypatch, tmp_path):
    g = _graph_with_index()
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)
    dest = tmp_path / "out.jsonld"
    out = mcp_server.export_jsonld("x", str(dest))
    assert dest.exists()
    doc = json.loads(dest.read_text(encoding="utf-8"))
    assert any(item.get("@type") == "Edge" for item in doc["@graph"])
    assert str(dest) in out


def test_export_jsonld_requires_overwrite(monkeypatch, tmp_path):
    g = _graph_with_index()
    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: g)
    dest = tmp_path / "out.jsonld"
    dest.write_text("KEEP-ME", encoding="utf-8")
    out = mcp_server.export_jsonld("x", str(dest))
    assert "overwrite" in out.lower()
    assert dest.read_text(encoding="utf-8") == "KEEP-ME"
    out = mcp_server.export_jsonld("x", str(dest), overwrite=True)
    assert dest.read_text(encoding="utf-8") != "KEEP-ME"
    assert str(dest) in out


def test_export_jsonld_rejects_non_graph(monkeypatch, tmp_path):
    class _ListKA:
        pass

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _ListKA())
    out = mcp_server.export_jsonld("x", str(tmp_path / "out.jsonld"))
    assert out == (
        "Graph export (GraphML/CSV/JSON-LD/Cypher) is only supported for graph-type "
        "knowledge abstracts (graph, hypergraph, temporal/spatial graphs)."
    )
    assert "JSON-LD" in out


def test_export_cypher_rejects_non_graph(monkeypatch, tmp_path):
    class _ListKA:
        pass

    monkeypatch.setattr(mcp_server, "_load_ka", lambda p: _ListKA())
    out = mcp_server.export_cypher("x", str(tmp_path / "out.cypher"))
    assert out == (
        "Graph export (GraphML/CSV/JSON-LD/Cypher) is only supported for graph-type "
        "knowledge abstracts (graph, hypergraph, temporal/spatial graphs)."
    )
    assert "Cypher" in out


# ---------------------------------------------------------------------------
# search / ask / export — load failures must return strings, not raise
# ---------------------------------------------------------------------------


def _mcp_load_tools(ka_path: str, dest):
    return (
        ("search", lambda: mcp_server.search(ka_path, "q")),
        ("ask", lambda: mcp_server.ask(ka_path, "q")),
        (
            "export_obsidian",
            lambda: mcp_server.export_obsidian(ka_path, str(dest / "vault")),
        ),
        (
            "export_graphml",
            lambda: mcp_server.export_graphml(ka_path, str(dest / "g.graphml")),
        ),
        ("export_csv", lambda: mcp_server.export_csv(ka_path, str(dest / "csv"))),
        (
            "export_jsonld",
            lambda: mcp_server.export_jsonld(ka_path, str(dest / "g.jsonld")),
        ),
        (
            "export_cypher",
            lambda: mcp_server.export_cypher(ka_path, str(dest / "g.cypher")),
        ),
    )


@pytest.mark.parametrize(
    "tool_name",
    [
        "search",
        "ask",
        "export_obsidian",
        "export_graphml",
        "export_csv",
        "export_jsonld",
        "export_cypher",
    ],
)
def test_load_missing_path_returns_string(tmp_path, tool_name):
    tools = dict(_mcp_load_tools(str(tmp_path / "nope"), tmp_path / "out"))
    out = tools[tool_name]()
    assert isinstance(out, str)
    assert out.startswith("Cannot load KA:")


@pytest.mark.parametrize(
    "tool_name",
    [
        "search",
        "ask",
        "export_obsidian",
        "export_graphml",
        "export_csv",
        "export_jsonld",
        "export_cypher",
    ],
)
def test_load_dir_without_data_json_returns_string(tmp_path, tool_name):
    empty = tmp_path / "empty_ka"
    empty.mkdir()
    tools = dict(_mcp_load_tools(str(empty), tmp_path / "out"))
    out = tools[tool_name]()
    assert isinstance(out, str)
    assert out.startswith("Cannot load KA:")
    assert "data.json" in out


@pytest.mark.parametrize(
    "tool_name",
    [
        "search",
        "ask",
        "export_obsidian",
        "export_graphml",
        "export_csv",
        "export_jsonld",
        "export_cypher",
    ],
)
def test_load_client_error_returns_string(tmp_path, monkeypatch, tool_name):
    ka = tmp_path / "ka"
    ka.mkdir()
    (ka / "data.json").write_text("{}", encoding="utf-8")
    (ka / "metadata.json").write_text(
        json.dumps({"template": "general/base_graph", "lang": "en"}),
        encoding="utf-8",
    )

    def _boom():
        raise ValueError("LLM API key is not configured")

    monkeypatch.setattr(mcp_server, "_get_clients", _boom)
    tools = dict(_mcp_load_tools(str(ka), tmp_path / "out"))
    out = tools[tool_name]()
    assert isinstance(out, str)
    assert out.startswith("Cannot load KA:")
    assert "not configured" in out


# ---------------------------------------------------------------------------
# FastMCP wiring (needs the optional `mcp` package)
# ---------------------------------------------------------------------------


def test_build_server_registers_tools():
    pytest.importorskip("mcp")
    server = mcp_server.build_server()
    assert server is not None
    assert server.name == "hyper-extract"
