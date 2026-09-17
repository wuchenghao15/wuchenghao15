from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from src import server


@pytest.mark.asyncio
async def test_memorize_passes_requested_dataset_name_to_client_memorize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []
    scheduled: list[asyncio.Task[None]] = []

    async def fake_add(content: str, dataset_name: str) -> None:
        calls.append(("add", {"content": content, "dataset_name": dataset_name}))

    async def fake_memorize(**kwargs: object) -> None:
        calls.append(("memorize", kwargs))

    original_create_task = asyncio.create_task

    def capture_task(coro: object) -> asyncio.Task[None]:
        task = original_create_task(coro)
        scheduled.append(task)
        return task

    monkeypatch.setattr(server, "_client", SimpleNamespace(add=fake_add, memorize=fake_memorize))
    monkeypatch.setattr(server.asyncio, "create_task", capture_task)

    result = await server.memorize("hello", dataset_name="beta")
    await asyncio.gather(*scheduled)

    assert len(result) == 1
    assert calls == [
        ("add", {"content": "hello", "dataset_name": "beta"}),
        ("memorize", {"datasets": ["beta"], "enable_content_routing": False}),
    ]
