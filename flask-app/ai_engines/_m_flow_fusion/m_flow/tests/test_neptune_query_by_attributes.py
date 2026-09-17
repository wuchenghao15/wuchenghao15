from __future__ import annotations

import asyncio

from m_flow.adapters.graph.neptune_driver.adapter import NeptuneGraphDB


class _TestableNeptuneGraphDB(NeptuneGraphDB):
    async def is_empty(self) -> bool:
        return False


def test_neptune_query_by_attributes_uses_all_filters_and_parameters() -> None:
    async def run() -> None:
        adapter = _TestableNeptuneGraphDB.__new__(_TestableNeptuneGraphDB)
        adapter._GRAPH_NODE_LABEL = "MFLOW_NODE"
        calls: list[tuple[str, dict | None]] = []

        async def fake_query(cypher: str, params: dict | None = None):
            calls.append((cypher, params))
            if len(calls) == 1:
                return [{"id": "node-1", "properties": {"type": "Entity", "status": "active"}}]
            return [{"source": "node-1", "target": "node-2", "type": "RELATED", "properties": {}}]

        adapter.query = fake_query

        nodes, edges = await adapter.query_by_attributes([{"type": ["Entity"]}, {"status": ["active"]}])

        assert nodes == [("node-1", {"type": "Entity", "status": "active"})]
        assert edges == [("node-1", "node-2", "RELATED", {})]
        assert len(calls) == 2

        node_cypher, node_params = calls[0]
        edge_cypher, edge_params = calls[1]

        assert "n.type IN $vals_0_type" in node_cypher
        assert "n.status IN $vals_1_status" in node_cypher
        assert "m.type IN $vals_0_type" in edge_cypher
        assert "m.status IN $vals_1_status" in edge_cypher
        assert node_params == {"vals_0_type": ["Entity"], "vals_1_status": ["active"]}
        assert edge_params == node_params

    asyncio.run(run())
