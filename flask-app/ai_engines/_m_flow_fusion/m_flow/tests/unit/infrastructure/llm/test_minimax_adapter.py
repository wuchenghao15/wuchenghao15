"""
Unit tests for MiniMaxAdapter — the MiniMax LLM backend.

These tests verify the adapter's contract without making real network calls.
Every external dependency (anthropic, instructor, rate-limiter) is mocked so
that the suite runs in < 1 s with zero side-effects.

The real ``extract_structured`` method is wrapped by a tenacity ``@retry``
decorator (120 s ceiling). To avoid test hangs, tests that exercise
``extract_structured`` patch the retry decorator away or mock the underlying
client directly so that the method either succeeds or raises on the first attempt.

References
----------
- MiniMaxAdapter source:   m_flow/llm/backends/litellm_instructor/llm/minimax/adapter.py
- LLMBackend protocol:     m_flow/llm/backends/litellm_instructor/llm/llm_interface.py
- AnthropicAdapter source: m_flow/llm/backends/litellm_instructor/llm/anthropic/adapter.py
"""

from __future__ import annotations

import asyncio
from contextlib import nullcontext
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

# The MiniMax adapter imports `anthropic` at module top-level (it speaks MiniMax's
# Anthropic-compatible endpoint). `anthropic` is declared as an OPTIONAL extra in
# pyproject.toml ([project.optional-dependencies] anthropic = ["anthropic>=0.26"]),
# so environments that do not install `m_flow[anthropic]` (e.g. the default CI matrix)
# would otherwise crash at collection time with ModuleNotFoundError. Skip the whole
# module cleanly when the optional dependency is absent.
pytest.importorskip(
    "anthropic",
    reason="MiniMax adapter requires the optional `anthropic` extra (install with `pip install m_flow[anthropic]`).",
)


# ---------------------------------------------------------------------------
# Pydantic response models used across tests
# ---------------------------------------------------------------------------
class SimpleResponse(BaseModel):
    """Minimal schema for structured output tests."""

    answer: str


class DetailedResponse(BaseModel):
    """Multi-field schema for richer extraction tests."""

    summary: str
    confidence: float
    tags: list[str]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MODULE = "m_flow.llm.backends.litellm_instructor.llm.minimax.adapter"
_MINIMAX_BASE_URL = "https://api.minimax.io/anthropic"
_DEFAULT_MODEL = "MiniMax-M2.7"


def _noop_rate_limiter():
    """Return a no-op async context manager that replaces the real limiter."""
    return nullcontext()


def _build_adapter(
    *,
    model: str = _DEFAULT_MODEL,
    max_tokens: int = 4096,
    instructor_mode: str | None = None,
    api_key: str = "test-minimax-key",
):
    """Construct a MiniMaxAdapter with mocked anthropic and instructor clients."""
    with (
        patch(f"{_MODULE}.instructor") as mock_instructor,
        patch(f"{_MODULE}.anthropic") as mock_anthropic,
        patch(f"{_MODULE}.get_llm_config") as mock_config,
    ):
        mock_cfg = MagicMock()
        mock_cfg.llm_api_key = api_key
        mock_config.return_value = mock_cfg

        mock_raw_client = MagicMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_raw_client

        mock_instructor.patch.return_value = MagicMock()
        mock_instructor.Mode = MagicMock(side_effect=lambda x: x)

        from m_flow.llm.backends.litellm_instructor.llm.minimax.adapter import MiniMaxAdapter

        adapter = MiniMaxAdapter(
            max_completion_tokens=max_tokens,
            model=model,
            instructor_mode=instructor_mode,
        )

        # Store mocks for assertion
        adapter._mock_anthropic = mock_anthropic
        adapter._mock_raw_client = mock_raw_client

    return adapter


# ---------------------------------------------------------------------------
# Test: Initialisation
# ---------------------------------------------------------------------------
class TestAdapterInit:
    """Verify constructor stores configuration correctly."""

    def test_default_model_is_minimax_m27(self):
        adapter = _build_adapter(model=None)
        assert adapter.model == _DEFAULT_MODEL

    def test_custom_model_stored(self):
        adapter = _build_adapter(model="MiniMax-M2.7-highspeed")
        assert adapter.model == "MiniMax-M2.7-highspeed"

    def test_max_completion_tokens_stored(self):
        adapter = _build_adapter(max_tokens=8192)
        assert adapter.max_completion_tokens == 8192

    def test_default_instructor_mode_is_anthropic_tools(self):
        with (
            patch(f"{_MODULE}.instructor") as mock_instructor,
            patch(f"{_MODULE}.anthropic"),
            patch(f"{_MODULE}.get_llm_config") as mock_config,
        ):
            mock_config.return_value = MagicMock(llm_api_key="key")
            mock_instructor.patch.return_value = MagicMock()
            captured_mode = []
            mock_instructor.Mode = MagicMock(side_effect=lambda x: captured_mode.append(x) or x)

            from m_flow.llm.backends.litellm_instructor.llm.minimax.adapter import MiniMaxAdapter

            MiniMaxAdapter(max_completion_tokens=4096)
            assert "anthropic_tools" in captured_mode

    def test_anthropic_client_uses_minimax_base_url(self):
        with (
            patch(f"{_MODULE}.instructor") as mock_instructor,
            patch(f"{_MODULE}.anthropic") as mock_anthropic,
            patch(f"{_MODULE}.get_llm_config") as mock_config,
        ):
            mock_config.return_value = MagicMock(llm_api_key="test-key")
            mock_instructor.patch.return_value = MagicMock()
            mock_instructor.Mode = MagicMock(side_effect=lambda x: x)

            from m_flow.llm.backends.litellm_instructor.llm.minimax.adapter import (
                MiniMaxAdapter,
                MINIMAX_BASE_URL,
            )

            MiniMaxAdapter(max_completion_tokens=4096)

            call_kwargs = mock_anthropic.AsyncAnthropic.call_args
            assert call_kwargs.kwargs["base_url"] == MINIMAX_BASE_URL

    def test_anthropic_client_uses_llm_api_key(self):
        with (
            patch(f"{_MODULE}.instructor") as mock_instructor,
            patch(f"{_MODULE}.anthropic") as mock_anthropic,
            patch(f"{_MODULE}.get_llm_config") as mock_config,
        ):
            mock_config.return_value = MagicMock(llm_api_key="sk-minimax-abc123")
            mock_instructor.patch.return_value = MagicMock()
            mock_instructor.Mode = MagicMock(side_effect=lambda x: x)

            from m_flow.llm.backends.litellm_instructor.llm.minimax.adapter import MiniMaxAdapter

            MiniMaxAdapter(max_completion_tokens=4096)

            call_kwargs = mock_anthropic.AsyncAnthropic.call_args
            assert call_kwargs.kwargs["api_key"] == "sk-minimax-abc123"

    def test_custom_instructor_mode_overrides_default(self):
        with (
            patch(f"{_MODULE}.instructor") as mock_instructor,
            patch(f"{_MODULE}.anthropic"),
            patch(f"{_MODULE}.get_llm_config") as mock_config,
        ):
            mock_config.return_value = MagicMock(llm_api_key="key")
            mock_instructor.patch.return_value = MagicMock()
            captured_mode = []
            mock_instructor.Mode = MagicMock(side_effect=lambda x: captured_mode.append(x) or x)

            from m_flow.llm.backends.litellm_instructor.llm.minimax.adapter import MiniMaxAdapter

            MiniMaxAdapter(max_completion_tokens=4096, instructor_mode="json_mode")
            assert "json_mode" in captured_mode
            assert "anthropic_tools" not in captured_mode


# ---------------------------------------------------------------------------
# Test: Protocol compliance
# ---------------------------------------------------------------------------
class TestProtocolCompliance:
    """Ensure MiniMaxAdapter satisfies the LLMBackend protocol."""

    def test_has_extract_structured_method(self):
        adapter = _build_adapter()
        assert hasattr(adapter, "extract_structured")
        assert callable(adapter.extract_structured)

    def test_runtime_checkable_protocol(self):
        from m_flow.llm.backends.litellm_instructor.llm.llm_interface import LLMBackend

        adapter = _build_adapter()
        assert isinstance(adapter, LLMBackend)

    def test_adapter_name_is_minimax(self):
        adapter = _build_adapter()
        assert adapter.name == "MiniMax"


# ---------------------------------------------------------------------------
# Test: extract_structured happy path
# ---------------------------------------------------------------------------
class TestExtractStructuredHappyPath:
    """Verify the main extract_structured method returns correct results."""

    @patch(f"{_MODULE}.llm_rate_limiter_context_manager", _noop_rate_limiter)
    def test_returns_validated_model(self):
        adapter = _build_adapter()
        expected = SimpleResponse(answer="42")
        adapter.aclient = AsyncMock(return_value=expected)

        result = asyncio.get_event_loop().run_until_complete(
            adapter.extract_structured("What is 6*7?", "Be precise.", SimpleResponse)
        )

        assert isinstance(result, SimpleResponse)
        assert result.answer == "42"

    @patch(f"{_MODULE}.llm_rate_limiter_context_manager", _noop_rate_limiter)
    def test_returns_complex_model(self):
        adapter = _build_adapter()
        expected = DetailedResponse(
            summary="Test summary",
            confidence=0.95,
            tags=["ai", "model"],
        )
        adapter.aclient = AsyncMock(return_value=expected)

        result = asyncio.get_event_loop().run_until_complete(
            adapter.extract_structured("Summarize this", "Extract info", DetailedResponse)
        )

        assert isinstance(result, DetailedResponse)
        assert result.summary == "Test summary"
        assert result.confidence == 0.95

    @patch(f"{_MODULE}.llm_rate_limiter_context_manager", _noop_rate_limiter)
    def test_merges_text_and_system_prompt(self):
        adapter = _build_adapter()
        mock_aclient = AsyncMock(return_value=SimpleResponse(answer="ok"))
        adapter.aclient = mock_aclient

        asyncio.get_event_loop().run_until_complete(
            adapter.extract_structured("user text", "system prompt", SimpleResponse)
        )

        call_kwargs = mock_aclient.call_args
        messages = call_kwargs.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "user text" in messages[0]["content"]
        assert "system prompt" in messages[0]["content"]

    @patch(f"{_MODULE}.llm_rate_limiter_context_manager", _noop_rate_limiter)
    def test_passes_correct_model(self):
        adapter = _build_adapter(model="MiniMax-M2.7-highspeed")
        mock_aclient = AsyncMock(return_value=SimpleResponse(answer="ok"))
        adapter.aclient = mock_aclient

        asyncio.get_event_loop().run_until_complete(adapter.extract_structured("text", "prompt", SimpleResponse))

        call_kwargs = mock_aclient.call_args
        assert call_kwargs.kwargs["model"] == "MiniMax-M2.7-highspeed"

    @patch(f"{_MODULE}.llm_rate_limiter_context_manager", _noop_rate_limiter)
    def test_passes_response_model(self):
        adapter = _build_adapter()
        mock_aclient = AsyncMock(return_value=DetailedResponse(summary="s", confidence=1.0, tags=[]))
        adapter.aclient = mock_aclient

        asyncio.get_event_loop().run_until_complete(adapter.extract_structured("text", "prompt", DetailedResponse))

        call_kwargs = mock_aclient.call_args
        assert call_kwargs.kwargs["response_model"] is DetailedResponse


# ---------------------------------------------------------------------------
# Test: Factory integration (create_llm_backend)
# ---------------------------------------------------------------------------
class TestFactoryIntegration:
    """Verify that the factory creates MiniMaxAdapter for 'minimax' provider."""

    @patch("m_flow.llm.utils.get_model_max_completion_tokens", return_value=None)
    @patch("m_flow.llm.backends.litellm_instructor.llm.get_llm_client.get_llm_config")
    @patch(f"{_MODULE}.instructor")
    @patch(f"{_MODULE}.anthropic")
    def test_minimax_provider_creates_minimax_adapter(
        self, mock_anthropic, mock_instructor, mock_config, mock_max_tokens
    ):
        mock_instructor.patch.return_value = MagicMock()
        mock_instructor.Mode = MagicMock(side_effect=lambda x: x)
        mock_anthropic.AsyncAnthropic.return_value = MagicMock()

        cfg = MagicMock()
        cfg.llm_provider = "minimax"
        cfg.llm_api_key = "sk-minimax-test"
        cfg.llm_model = "MiniMax-M2.7"
        cfg.llm_max_completion_tokens = 4096
        cfg.llm_instructor_mode = ""
        mock_config.return_value = cfg

        from m_flow.llm.backends.litellm_instructor.llm.get_llm_client import create_llm_backend
        from m_flow.llm.backends.litellm_instructor.llm.minimax.adapter import MiniMaxAdapter

        backend = create_llm_backend(raise_api_key_error=False)

        assert isinstance(backend, MiniMaxAdapter)
        assert backend.model == "MiniMax-M2.7"

    def test_minimax_in_provider_enum(self):
        from m_flow.llm.backends.litellm_instructor.llm.get_llm_client import LLMProvider

        assert LLMProvider.MINIMAX == "minimax"
        assert LLMProvider("minimax") == LLMProvider.MINIMAX

    def test_minimax_models_list(self):
        from m_flow.llm.backends.litellm_instructor.llm.minimax.adapter import MINIMAX_MODELS

        assert "MiniMax-M2.7" in MINIMAX_MODELS
        assert "MiniMax-M2.7-highspeed" in MINIMAX_MODELS
        assert len(MINIMAX_MODELS) == 2

    def test_minimax_base_url(self):
        from m_flow.llm.backends.litellm_instructor.llm.minimax.adapter import MINIMAX_BASE_URL

        assert MINIMAX_BASE_URL.startswith("https://api.minimax.io")
        assert "anthropic" in MINIMAX_BASE_URL
