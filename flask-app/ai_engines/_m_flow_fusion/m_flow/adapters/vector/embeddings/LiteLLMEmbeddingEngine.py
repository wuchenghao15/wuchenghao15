"""
LiteLLM-based embedding engine.

Supports OpenAI, Azure, and other LiteLLM-compatible providers.
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
from typing import List, Optional

import litellm
import numpy as np
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_delay,
    wait_exponential_jitter,
)

from m_flow.adapters.exceptions import EmbeddingException
from m_flow.adapters.vector.embeddings.EmbeddingEngine import EmbeddingEngine
from m_flow.llm.tokenizer.HuggingFace import HuggingFaceTokenizer
from m_flow.llm.tokenizer.Mistral import MistralTokenizer
from m_flow.llm.tokenizer.TikToken import TikTokenTokenizer
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.rate_limiting import embedding_rate_limiter_context_manager

litellm.set_verbose = False
_log = get_logger("LiteLLMEmbeddingEngine")


class LiteLLMEmbeddingEngine(EmbeddingEngine):
    """
    Embedding engine using LiteLLM backend.

    Handles context window limits by splitting and pooling
    embeddings for oversized inputs.
    """

    _RETRY_LIMIT = 5

    def __init__(
        self,
        model: Optional[str] = "openai/text-embedding-3-large",
        provider: str = "openai",
        dimensions: Optional[int] = 3072,
        api_key: str = None,
        endpoint: str = None,
        api_version: str = None,
        max_completion_tokens: int = 512,
        batch_size: int = 100,
    ):
        self.model = model
        self.provider = provider
        self.dimensions = dimensions
        self.api_key = api_key
        self.endpoint = endpoint
        self.api_version = api_version
        self.max_completion_tokens = max_completion_tokens
        self.batch_size = batch_size
        self.tokenizer = self._init_tokenizer()

        # Mock mode for testing
        mock_env = os.getenv("MOCK_EMBEDDING", "false")
        self.mock = mock_env.lower() in ("true", "1", "yes")

    @retry(
        stop=stop_after_delay(128),
        wait=wait_exponential_jitter(2, 128),
        retry=retry_if_not_exception_type(
            (
                litellm.exceptions.NotFoundError,
                litellm.exceptions.BadRequestError,
                litellm.exceptions.AuthenticationError,
            )
        ),
        before_sleep=before_sleep_log(_log, logging.DEBUG),
        reraise=True,
    )
    async def embed_text(self, text: List[str]) -> List[List[float]]:
        """
        Generate embeddings for input texts.

        Handles context window overflow by splitting and pooling.
        """
        try:
            if self.mock:
                return [[0.0] * self.dimensions for _ in text]

            async with embedding_rate_limiter_context_manager():
                resp = await litellm.aembedding(
                    model=self.model,
                    input=text,
                    api_key=self.api_key,
                    api_base=self.endpoint,
                    api_version=self.api_version,
                )

            return [d["embedding"] for d in resp.data]

        except litellm.exceptions.ContextWindowExceededError:
            return await self._handle_context_overflow(text)

        except (litellm.exceptions.BadRequestError, litellm.exceptions.NotFoundError) as e:
            _log.error(f"Embedding error ({self.model}): {e}")
            raise EmbeddingException(f"Embedding failed for model {self.model}") from e

    async def _handle_context_overflow(self, text: List[str]) -> List[List[float]]:
        """Split and pool embeddings for oversized input."""
        if len(text) > 1:
            # Split batch in half
            mid = math.ceil(len(text) / 2)
            left_vecs, right_vecs = await asyncio.gather(
                self.embed_text(text[:mid]),
                self.embed_text(text[mid:]),
            )
            return left_vecs + right_vecs

        if len(text) == 1:
            # Single oversized string - split with overlap and pool
            s = text[0]
            third = len(s) // 3
            left_part, right_part = s[: third * 2], s[third:]

            (left_vec,), (right_vec,) = await asyncio.gather(
                self.embed_text([left_part]),
                self.embed_text([right_part]),
            )

            pooled = (np.array(left_vec) + np.array(right_vec)) / 2
            return [pooled.tolist()]

        raise litellm.exceptions.ContextWindowExceededError("Cannot split empty input")

    def get_vector_size(self) -> int:
        return self.dimensions

    def get_batch_size(self) -> int:
        return self.batch_size

    def _init_tokenizer(self):
        """Select appropriate tokenizer for provider."""
        model_name = self.model.split("/")[-1]

        if "openai" in self.provider.lower():
            try:
                return TikTokenTokenizer(model=model_name, max_completion_tokens=self.max_completion_tokens)
            except KeyError:
                # Non-OpenAI model served via OpenAI-compatible API (e.g. BGE-M3, Jina)
                _log.info(f"Model '{model_name}' not in tiktoken registry, using cl100k_base fallback")
                return TikTokenTokenizer(model=None, max_completion_tokens=self.max_completion_tokens)

        if "gemini" in self.provider.lower():
            return TikTokenTokenizer(model=None, max_completion_tokens=self.max_completion_tokens)

        if "mistral" in self.provider.lower():
            return MistralTokenizer(model=model_name, max_completion_tokens=self.max_completion_tokens)

        # Fallback to HuggingFace tokenizer
        try:
            return HuggingFaceTokenizer(
                model=self.model.replace("hosted_vllm/", ""),
                max_completion_tokens=self.max_completion_tokens,
            )
        except Exception as e:
            _log.warning(f"HuggingFace tokenizer failed: {e}, using TikToken")
            return TikTokenTokenizer(model=None, max_completion_tokens=self.max_completion_tokens)
