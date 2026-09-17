from __future__ import annotations

import asyncio

from m_flow.adapters.graph.neptune_driver.adapter import NeptuneGraphDB


def test_neptune_has_edges_returns_matching_edge_tuples() -> None:
    class TestableNeptuneGraphDB(NeptuneGraphDB):
        async def is_empty(self) -> bool:
            return False

    async def run() -> None:
        adapter = TestableNeptuneGraphDB.__new__(TestableNeptuneGraphDB)
        adapter._GRAPH_NODE_LABEL = "MFLOW_NODE"

        async def fake_query(_cypher: str, _params: dict):
            return [
                {"src": "a", "tgt": "b", "rel": "LIKES", "found": True},
                {"src": "x", "tgt": "y", "rel": "KNOWS", "found": False},
                {"src": "b", "tgt": "c", "rel": "MENTIONS", "found": True},
            ]

        adapter.query = fake_query

        result = await adapter.has_edges(
            [
                ("a", "b", "LIKES"),
                ("x", "y", "KNOWS"),
                ("b", "c", "MENTIONS"),
            ]
        )

        assert result == [("a", "b", "LIKES"), ("b", "c", "MENTIONS")]

    asyncio.run(run())
