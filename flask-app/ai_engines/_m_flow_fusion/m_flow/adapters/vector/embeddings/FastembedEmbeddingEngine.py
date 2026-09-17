"""FastEmbed-based local embedding adapter for M-Flow.

Runs ONNX-optimised embedding models on the local machine via the
``fastembed`` library — no external API calls required.  Retry logic is
handled by *tenacity* with exponential-jitter back-off.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

import litellm
from fastembed import TextEmbedding
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_delay,
    wait_exponential_jitter,
)

from m_flow.adapters.exceptions import EmbeddingException
from m_flow.adapters.vector.embeddings.EmbeddingEngine import EmbeddingEngine
from m_flow.llm.tokenizer.TikToken import TikTokenTokenizer
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.rate_limiting import embedding_rate_limiter_context_manager

litellm.set_verbose = False

_adapter_log = get_logger("m_flow.adapters.fastembed")


class FastembedEmbeddingEngine(EmbeddingEngine):
    """Local embedding engine powered by FastEmbed / ONNX Runtime.

    Embeds text on-device without requiring any remote service.  When
    ``MOCK_EMBEDDING`` is set in the environment, zero-vectors are
    returned to speed up automated test runs.
    """

    __slots__ = (
        "model",
        "dimensions",
        "max_completion_tokens",
        "batch_size",
        "embedding_model",
        "tokenizer",
        "mock",
    )

    def __init__(
        self,
        model: Optional[str] = "openai/text-embedding-3-large",
        dimensions: Optional[int] = 3072,
        max_completion_tokens: int = 512,
        batch_size: int = 100,
    ):
        self.model = model
        self.dimensions = dimensions
        self.max_completion_tokens = max_completion_tokens
        self.batch_size = batch_size

        self.embedding_model = TextEmbedding(model_name=model)
        self.tokenizer = self._init_tokenizer()

        mock_raw = os.getenv("MOCK_EMBEDDING", "false")
        self.mock = mock_raw.lower() in {"true", "1", "yes"}

    # ------------------------------------------------------------------
    # Public API
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
        before_sleep=before_sleep_log(_adapter_log, logging.DEBUG),
        reraise=True,
    )
    async def embed_text(self, text: List[str]) -> List[List[float]]:
        """Produce dense vectors for every string in *text*."""
        try:
            if self.mock:
                vec_dim = self.dimensions
                return [[0.0] * vec_dim for _ in text]

            async with embedding_rate_limiter_context_manager():
                raw_vectors = self.embedding_model.embed(
                    text,
                    batch_size=len(text),
                    parallel=None,
                )

            return list(raw_vectors)

        except Exception as exc:
            _adapter_log.error(
                "FastEmbed embedding failed for model %s: %s",
                self.model,
                exc,
            )
            raise EmbeddingException(f"Unable to compute embeddings with {self.model}") from exc

    def get_vector_size(self) -> int:
        return self.dimensions

    def get_batch_size(self) -> int:
        return self.batch_size

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _init_tokenizer(self):
        """Prepare a TikToken tokenizer for input pre-processing."""
        return TikTokenTokenizer(
            model="gpt-4o",
            max_completion_tokens=self.max_completion_tokens,
        )
