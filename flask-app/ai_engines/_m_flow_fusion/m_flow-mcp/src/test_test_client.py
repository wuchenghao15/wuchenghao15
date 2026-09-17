from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.test_client import MCPTestClient


class _FakeSession:
    def __init__(self, text: str) -> None:
        self._text = text

    async def call_tool(self, name: str, arguments: dict | None = None) -> SimpleNamespace:
        return SimpleNamespace(content=[SimpleNamespace(text=self._text)])


@pytest.mark.asyncio
async def test_learn_records_failure_for_unexpected_response_content() -> None:
    client = MCPTestClient()

    await client._test_learn(_FakeSession("totally unrelated response"))

    assert client.results["learn"]["status"] == "FAIL"
    assert "未预期的返回" in client.results["learn"]["error"]


@pytest.mark.asyncio
async def test_learn_with_params_records_failure_for_unexpected_response_content() -> None:
    client = MCPTestClient()

    await client._test_learn_with_params(_FakeSession("totally unrelated response"))

    assert client.results["learn_with_params"]["status"] == "FAIL"
    assert "未预期的返回" in client.results["learn_with_params"]["error"]
