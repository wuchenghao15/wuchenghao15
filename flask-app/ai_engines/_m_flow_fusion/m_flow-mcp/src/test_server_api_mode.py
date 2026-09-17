from __future__ import annotations

from types import SimpleNamespace

import pytest

from src import server


@pytest.mark.asyncio
async def test_search_uses_remote_flag_for_api_mode_formatting(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search(**_: object) -> list[str]:
        return ["remote-result"]

    fake_client = SimpleNamespace(_remote=True, search=fake_search)
    monkeypatch.setattr(server, "_client", fake_client)

    result = await server.search("hello", "EPISODIC")

    assert len(result) == 1
    assert result[0].text == "['remote-result']"


@pytest.mark.asyncio
async def test_list_data_rejects_dataset_detail_in_api_mode_without_attribute_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = SimpleNamespace(_remote=True)
    monkeypatch.setattr(server, "_client", fake_client)

    result = await server.list_data("11111111-1111-1111-1111-111111111111")

    assert len(result) == 1
    assert "API模式不支持详细数据列表" in result[0].text
