"""
Embedding engine factory.

Creates and caches embedding engine instances based on configuration.
"""

from __future__ import annotations

from functools import lru_cache

from m_flow.adapters.vector.embeddings.config import get_embedding_config
from m_flow.llm.config import get_llm_config
from .EmbeddingEngine import EmbeddingEngine


def get_embedding_engine() -> EmbeddingEngine:
    """
    Get configured embedding engine singleton.

    Uses LRU cache to ensure the same engine instance is reused,
    preventing excessive API connections.
    """
    cfg = get_embedding_config()
    llm_cfg = get_llm_config()

    return _build_engine(
        provider=cfg.embedding_provider,
        model=cfg.embedding_model,
        dimensions=cfg.embedding_dimensions,
        max_tokens=cfg.embedding_max_completion_tokens,
        endpoint=cfg.embedding_endpoint,
        api_key=cfg.embedding_api_key,
        api_version=cfg.embedding_api_version,
        batch_size=cfg.embedding_batch_size,
        hf_tokenizer=cfg.huggingface_tokenizer,
        llm_api_key=llm_cfg.llm_api_key,
        llm_provider=llm_cfg.llm_provider,
    )


@lru_cache
def _build_engine(
    provider: str,
    model: str,
    dimensions: int,
    max_tokens: int,
    endpoint: str | None,
    api_key: str | None,
    api_version: str | None,
    batch_size: int,
    hf_tokenizer: str | None,
    llm_api_key: str | None,
    llm_provider: str | None,
) -> EmbeddingEngine:
    """
    Instantiate embedding engine based on provider.

    Supports: fastembed, ollama, or LiteLLM-based providers.
    """
    # FastEmbed - local embedding
    if provider == "fastembed":
        from .FastembedEmbeddingEngine import FastembedEmbeddingEngine

        return FastembedEmbeddingEngine(
            model=model,
            dimensions=dimensions,
            max_completion_tokens=max_tokens,
            batch_size=batch_size,
        )

    # Ollama - local LLM server
    if provider == "ollama":
        from .OllamaEmbeddingEngine import OllamaEmbeddingEngine

        return OllamaEmbeddingEngine(
            model=model,
            dimensions=dimensions,
            max_completion_tokens=max_tokens,
            endpoint=endpoint,
            huggingface_tokenizer=hf_tokenizer,
            batch_size=batch_size,
        )

    # LiteLLM - OpenAI-compatible providers
    from .LiteLLMEmbeddingEngine import LiteLLMEmbeddingEngine

    # Determine which API key to use
    effective_key = api_key or (api_key if llm_provider == "custom" else llm_api_key)

    return LiteLLMEmbeddingEngine(
        provider=provider,
        api_key=effective_key,
        endpoint=endpoint,
        api_version=api_version,
        model=model,
        dimensions=dimensions,
        max_completion_tokens=max_tokens,
        batch_size=batch_size,
    )
