"""Ollama-backed embedding adapter for M-Flow.

Calls a local (or remote) Ollama instance to produce dense vector
representations.  Retries with exponential-jitter back-off on transient
HTTP failures via *tenacity*.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import List, Optional

import aiohttp
import litellm
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_delay,
    wait_exponential_jitter,
)

from m_flow.adapters.vector.embeddings.EmbeddingEngine import EmbeddingEngine
from m_flow.llm.tokenizer.HuggingFace import HuggingFaceTokenizer
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.rate_limiting import embedding_rate_limiter_context_manager
from m_flow.shared.utils import create_secure_ssl_context

_engine_log = get_logger("m_flow.adapters.ollama_embed")

_OLLAMA_DEFAULT_URL = "http://localhost:11434/api/embeddings"
_OLLAMA_DEFAULT_MODEL = "avr/sfr-embedding-mistral:latest"
_HTTP_TIMEOUT_SECS = 60.0


class OllamaEmbeddingEngine(EmbeddingEngine):
    """Produce embeddings through an Ollama server.

    Supports any embedding model hosted by Ollama.  When the environment
    variable ``MOCK_EMBEDDING`` is truthy the engine returns zero-vectors
    instead of making real HTTP calls – useful for tests.
    """

    __slots__ = (
        "model",
        "dimensions",
        "max_completion_tokens",
        "endpoint",
        "hf_tokenizer_name",
        "batch_size",
        "tokenizer",
        "mock",
    )

    def __init__(
        self,
        model: Optional[str] = None,
        dimensions: Optional[int] = 1024,
        max_completion_tokens: int = 512,
        endpoint: Optional[str] = None,
        huggingface_tokenizer: str = "Salesforce/SFR-Embedding-Mistral",
        batch_size: int = 100,
    ):
        self.model = model if model is not None else _OLLAMA_DEFAULT_MODEL
        self.dimensions = dimensions
        self.max_completion_tokens = max_completion_tokens
        self.endpoint = endpoint if endpoint is not None else _OLLAMA_DEFAULT_URL
        self.hf_tokenizer_name = huggingface_tokenizer
        self.batch_size = batch_size

        self.tokenizer = self._init_tokenizer()

        mock_flag = os.getenv("MOCK_EMBEDDING", "false")
        self.mock = mock_flag.lower() in {"true", "1", "yes"}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed_text(self, text: List[str]) -> List[List[float]]:
        """Embed every string in *text* and return the resulting vectors."""
        if self.mock:
            dim = self.dimensions
            return [[0.0] * dim for _ in text]

        coroutines = [self._request_single_vector(t) for t in text]
        return await asyncio.gather(*coroutines)

    def get_vector_size(self) -> int:
        return self.dimensions

    def get_batch_size(self) -> int:
        return self.batch_size

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_delay(128),
        wait=wait_exponential_jitter(8, 128),
        retry=retry_if_not_exception_type(
            (
                litellm.exceptions.NotFoundError,
                litellm.exceptions.BadRequestError,
                litellm.exceptions.AuthenticationError,
            )
        ),
        before_sleep=before_sleep_log(_engine_log, logging.DEBUG),
        reraise=True,
    )
    async def _request_single_vector(self, input_text: str) -> List[float]:
        """POST a single prompt to the Ollama embeddings endpoint."""
        body = {
            "model": self.model,
            "prompt": input_text,
            "input": input_text,
        }

        auth_headers: dict[str, str] = {}
        api_token = os.getenv("LLM_API_KEY")
        if api_token:
            auth_headers["Authorization"] = f"Bearer {api_token}"

        tls_ctx = create_secure_ssl_context()
        tcp = aiohttp.TCPConnector(ssl=tls_ctx)

        async with aiohttp.ClientSession(connector=tcp) as http:
            async with embedding_rate_limiter_context_manager():
                async with http.post(
                    self.endpoint,
                    json=body,
                    headers=auth_headers,
                    timeout=_HTTP_TIMEOUT_SECS,
                ) as response:
                    payload = await response.json()

                    if "embeddings" in payload:
                        return payload["embeddings"][0]
                    return payload["data"][0]["embedding"]

    def _init_tokenizer(self):
        """Build the HuggingFace tokenizer used for prompt truncation."""
        _engine_log.debug("Initialising HF tokenizer: %s", self.hf_tokenizer_name)
        return HuggingFaceTokenizer(
            model=self.hf_tokenizer_name,
            max_completion_tokens=self.max_completion_tokens,
        )
