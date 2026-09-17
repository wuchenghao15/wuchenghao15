from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from m_flow_client import MflowClient


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_remote_get_workflow_status_uses_datasets_status_endpoint():
    dataset_id = uuid4()
    expected = {str(dataset_id): "DATASET_PROCESSING_COMPLETED"}

    client = MflowClient(server_url="https://example.test", auth_token="secret-token")

    captured = {}

    async def fake_get(url, params=None, headers=None):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        return DummyResponse(expected)

    client._http = SimpleNamespace(get=fake_get)

    result = await client.get_workflow_status([dataset_id], "memorize_pipeline")

    assert result == expected
    assert captured["url"] == "https://example.test/api/v1/datasets/status"
    assert captured["params"] == [("dataset", str(dataset_id))]
    assert captured["headers"]["Authorization"] == "Bearer secret-token"


@pytest.mark.asyncio
async def test_remote_get_workflow_status_returns_empty_mapping_for_non_dict_payload():
    dataset_id = uuid4()

    client = MflowClient(server_url="https://example.test")

    async def fake_get(url, params=None, headers=None):
        return DummyResponse(["unexpected", "payload"])

    client._http = SimpleNamespace(get=fake_get)

    result = await client.get_workflow_status([dataset_id], "memorize_pipeline")

    assert result == {}
