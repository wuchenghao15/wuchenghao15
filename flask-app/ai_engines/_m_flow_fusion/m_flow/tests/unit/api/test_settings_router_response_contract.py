"""Regression tests for the settings API response contract."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient


def test_settings_response_masks_api_keys_and_omits_internal_fields(monkeypatch):
    """GET /api/v1/settings should expose only the public, redacted contract."""
    llm_key = "test-llm-key-1234567890"
    vector_key = "test-vector-key-1234567890"
    baml_key = "test-baml-key-1234567890"
    fallback_key = "test-fallback-key-1234567890"

    monkeypatch.setenv("MFLOW_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("MFLOW_LLM_MODEL", "claude-haiku-4-5")
    monkeypatch.setenv("MFLOW_LLM_API_KEY", llm_key)
    monkeypatch.setenv("MFLOW_BAML_LLM_API_KEY", baml_key)
    monkeypatch.setenv("MFLOW_FALLBACK_API_KEY", fallback_key)
    monkeypatch.setenv("MFLOW_VECTOR_DB_PROVIDER", "lancedb")
    monkeypatch.setenv("MFLOW_VECTOR_DB_URL", "/tmp/mflow-test-settings.lancedb")
    monkeypatch.setenv("MFLOW_VECTOR_DB_KEY", vector_key)

    from m_flow.adapters.vector.config import get_vectordb_config
    from m_flow.api.client import app
    from m_flow.auth.methods import get_authenticated_user
    from m_flow.llm.config import get_llm_config

    get_llm_config.cache_clear()
    get_vectordb_config.cache_clear()

    async def mock_auth():
        return SimpleNamespace(id=uuid4(), email="settings@test.local", is_active=True, tenant_id=uuid4())

    app.dependency_overrides[get_authenticated_user] = mock_auth
    try:
        response = TestClient(app).get("/api/v1/settings")
    finally:
        app.dependency_overrides.clear()
        get_llm_config.cache_clear()
        get_vectordb_config.cache_clear()

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["llm"]["llmProvider"] == "anthropic"
    assert payload["llm"]["llmModel"] == "claude-haiku-4-5"
    assert payload["llm"]["llmApiKey"] != llm_key
    assert payload["llm"]["llmApiKey"].startswith(llm_key[:10])
    assert set(payload["llm"]) == {
        "llmProvider",
        "llmModel",
        "llmEndpoint",
        "llmApiVersion",
        "llmApiKey",
    }

    assert payload["vectorDb"]["vectorDbProvider"] == "lancedb"
    assert payload["vectorDb"]["vectorDbUrl"] == "/tmp/mflow-test-settings.lancedb"
    assert payload["vectorDb"]["vectorDbKey"] != vector_key
    assert payload["vectorDb"]["vectorDbKey"].startswith(vector_key[:10])
    assert set(payload["vectorDb"]) == {
        "vectorDbProvider",
        "vectorDbUrl",
        "vectorDbKey",
    }

    assert "bamlLlmApiKey" not in payload["llm"]
    assert "fallbackApiKey" not in payload["llm"]
