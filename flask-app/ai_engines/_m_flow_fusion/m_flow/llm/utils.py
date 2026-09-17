"""M-Flow LLM helpers — token arithmetic and connectivity probes.

Centralises logic that multiple M-Flow subsystems need, such as
determining safe chunk sizes and smoke-testing remote model endpoints.
"""

from __future__ import annotations

from typing import Optional

import litellm

from m_flow.llm.LLMGateway import LLMService
from m_flow.llm.backends.litellm_instructor.llm.get_llm_client import (
    create_llm_backend,
)
from m_flow.shared.logging_utils import get_logger

_logger = get_logger()


# ======================================================================
# Token-budget utilities
# ======================================================================


def get_max_chunk_tokens() -> int:
    """Derive the largest token count a single text chunk may have.

    The value is the **minimum** of two constraints:

    1. The embedding model's own ``max_completion_tokens`` ceiling.
    2. Half the LLM's maximum context window — reserving the other half
       for the model's generated reply.

    Returns
    -------
    int
        Maximum tokens per chunk that satisfies both constraints.

    Note
    ----
    The import of the vector engine is deferred to runtime to break an
    otherwise circular dependency between the LLM and vector packages.
    """
    from m_flow.adapters.vector import get_vector_provider

    embedding_backend = get_vector_provider().embedding_engine
    language_model = create_llm_backend(raise_api_key_error=False)

    half_llm_context = language_model.max_completion_tokens // 2
    embedding_cap = embedding_backend.max_completion_tokens

    return min(embedding_cap, half_llm_context)


def get_model_max_completion_tokens(model_name: str) -> Optional[int]:
    """Look up the advertised token ceiling for *model_name*.

    Consults the ``litellm.model_cost`` registry that ships with
    LiteLLM.  If the model is not catalogued there, ``None`` is
    returned so the caller can fall back to a sensible default.

    Parameters
    ----------
    model_name:
        Canonical model identifier (e.g. ``"gpt-4"``).

    Returns
    -------
    int or None
        Token limit when known; ``None`` otherwise.
    """
    registry = litellm.model_cost

    if model_name not in registry:
        _logger.debug("Model '%s' absent from LiteLLM registry", model_name)
        return None

    ceiling = registry[model_name]["max_tokens"]
    _logger.debug("Token ceiling for %s is %d", model_name, ceiling)
    return ceiling


# ======================================================================
# Connectivity smoke-tests
# ======================================================================


async def test_llm_connection() -> None:
    """Fire a trivial structured-output request to verify LLM reachability.

    Raises
    ------
    Exception
        Propagated from the LLM adapter if the request fails for any
        reason (network, auth, rate-limit …).
    """
    try:
        await LLMService.extract_structured(
            text_input="test",
            system_prompt='Respond with: "test"',
            response_model=str,
        )
    except Exception as exc:
        _logger.error("LLM connectivity probe failed: %s", exc)
        raise


async def test_embedding_connection() -> None:
    """Send a one-word embedding request to verify the vector backend.

    Raises
    ------
    Exception
        Propagated from the embedding engine when the probe fails.
    """
    try:
        from m_flow.adapters.vector import get_vector_provider

        vector_backend = get_vector_provider()
        await vector_backend.embedding_engine.embed_text("test")
    except Exception as exc:
        _logger.error("Embedding connectivity probe failed: %s", exc)
        raise
