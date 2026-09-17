from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_user():
    return SimpleNamespace(
        id=uuid4(),
        email="responses_test@example.com",
        is_active=True,
        is_verified=True,
        tenant_id=uuid4(),
        is_superuser=False,
    )


@pytest.fixture
def test_client(mock_user):
    from m_flow.api.client import app
    from m_flow.auth.methods import get_authenticated_user

    async def mock_auth():
        return mock_user

    app.dependency_overrides[get_authenticated_user] = mock_auth
    client = TestClient(app, raise_server_exceptions=False)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


class TestResponsesRouterModelResolution:
    @pytest.mark.asyncio
    async def test_default_alias_uses_configured_model(self, monkeypatch, test_client):
        responses_router = importlib.import_module("m_flow.api.v1.responses.routers.get_responses_router")

        create_mock = AsyncMock(
            return_value=MagicMock(
                model_dump=lambda: {
                    "id": "resp_alias",
                    "output": [],
                    "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
                }
            )
        )
        client_mock = MagicMock()
        client_mock.responses.create = create_mock

        monkeypatch.setattr(
            responses_router,
            "get_llm_config",
            lambda: SimpleNamespace(llm_api_key="test-key", llm_model="gpt-5-mini"),
        )
        monkeypatch.setattr(
            responses_router.openai,
            "AsyncOpenAI",
            lambda api_key: client_mock,
        )

        response = test_client.post(
            "/api/v1/responses/",
            json={
                "model": "m_flow-v1",
                "input": "Say hi",
                "tools": [],
                "temperature": 0,
            },
        )

        assert response.status_code == 200, response.text
        assert create_mock.await_args.kwargs["model"] == "gpt-5-mini"
        assert response.json()["model"] == "gpt-5-mini"

    @pytest.mark.asyncio
    async def test_explicit_model_is_forwarded_to_provider(self, monkeypatch, test_client):
        responses_router = importlib.import_module("m_flow.api.v1.responses.routers.get_responses_router")

        create_mock = AsyncMock(
            return_value=MagicMock(
                model_dump=lambda: {
                    "id": "resp_explicit",
                    "model": "gpt-4.1-mini",
                    "output": [],
                    "usage": {"input_tokens": 7, "output_tokens": 4, "total_tokens": 11},
                }
            )
        )
        client_mock = MagicMock()
        client_mock.responses.create = create_mock

        monkeypatch.setattr(
            responses_router,
            "get_llm_config",
            lambda: SimpleNamespace(llm_api_key="test-key", llm_model="gpt-5-mini"),
        )
        monkeypatch.setattr(
            responses_router.openai,
            "AsyncOpenAI",
            lambda api_key: client_mock,
        )

        response = test_client.post(
            "/api/v1/responses/",
            json={
                "model": "gpt-4.1-mini",
                "input": "Summarize this",
                "tools": [],
                "temperature": 0,
            },
        )

        assert response.status_code == 200, response.text
        assert create_mock.await_args.kwargs["model"] == "gpt-4.1-mini"
        assert response.json()["model"] == "gpt-4.1-mini"
