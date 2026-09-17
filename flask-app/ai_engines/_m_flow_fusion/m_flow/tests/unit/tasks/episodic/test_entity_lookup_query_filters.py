from __future__ import annotations

import asyncio

from m_flow.memory.episodic.utils import entity_lookup


class FakeGraphProvider:
    def __init__(self, nodes):
        self.nodes = nodes
        self.calls = []

    async def query_by_attributes(self, filters):
        self.calls.append(filters)
        return self.nodes, []


def test_find_existing_entities_queries_specific_canonical_name(monkeypatch) -> None:
    async def run() -> None:
        provider = FakeGraphProvider(
            [
                ("entity-1", {"name": "Alice", "description": "Engineer", "canonical_name": "alice"}),
                ("entity-2", {"name": "Bob", "description": "Designer", "canonical_name": "bob"}),
            ]
        )

        async def fake_get_graph_provider():
            return provider

        monkeypatch.setattr(entity_lookup, "get_graph_provider", fake_get_graph_provider)

        result = await entity_lookup.find_existing_entities_by_canonical_name("alice")

        assert provider.calls == [[{"type": ["Entity"], "canonical_name": ["alice"]}]]
        assert result == [
            {
                "id": "entity-1",
                "name": "Alice",
                "description": "Engineer",
                "canonical_name": "alice",
            }
        ]

    asyncio.run(run())


def test_batch_find_queries_only_requested_canonical_names(monkeypatch) -> None:
    async def run() -> None:
        provider = FakeGraphProvider(
            [
                ("entity-1", {"name": "Alice", "description": "Engineer", "canonical_name": "alice"}),
                ("entity-2", {"name": "Bob", "description": "Designer", "canonical_name": "bob"}),
                ("entity-3", {"name": "Ignored", "description": "Other", "canonical_name": "carol"}),
            ]
        )

        async def fake_get_graph_provider():
            return provider

        monkeypatch.setattr(entity_lookup, "get_graph_provider", fake_get_graph_provider)

        result = await entity_lookup.batch_find_existing_entities_by_canonical_names(
            ["alice", "bob"], exclude_ids=["entity-2"]
        )

        assert provider.calls == [[{"type": ["Entity"], "canonical_name": ["alice", "bob"]}]]
        assert result == {
            "alice": [
                {
                    "id": "entity-1",
                    "name": "Alice",
                    "description": "Engineer",
                    "canonical_name": "alice",
                }
            ],
            "bob": [],
        }

    asyncio.run(run())
