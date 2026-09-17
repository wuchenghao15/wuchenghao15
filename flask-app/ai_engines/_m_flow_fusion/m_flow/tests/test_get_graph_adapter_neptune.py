from __future__ import annotations

import importlib
import types

from m_flow.adapters.graph import get_graph_adapter


def test_neptune_adapter_exports_endpoint_prefix_constant() -> None:
    neptune_adapter = importlib.import_module("m_flow.adapters.graph.neptune_driver.adapter")

    assert neptune_adapter.NEPTUNE_ENDPOINT_URL == "neptune-graph://"


def test_build_adapter_constructs_neptune_graph_from_prefixed_url(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class FakeNeptuneGraphDB:
        def __init__(self, graph_id: str) -> None:
            captured["graph_id"] = graph_id

    get_graph_adapter._build_adapter.cache_clear()
    monkeypatch.setattr(get_graph_adapter, "_ensure_langchain_aws", lambda: None)

    real_module = importlib.import_module("m_flow.adapters.graph.neptune_driver.adapter")
    monkeypatch.setattr(real_module, "NeptuneGraphDB", FakeNeptuneGraphDB)

    adapter = get_graph_adapter._build_adapter(
        graph_database_provider="neptune",
        graph_database_url="neptune-graph://demo-graph",
    )

    assert isinstance(adapter, FakeNeptuneGraphDB)
    assert captured == {"graph_id": "demo-graph"}
