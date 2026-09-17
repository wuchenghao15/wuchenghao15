"""
Asynchronous rate-limiting helpers for LLM and embedding calls.

Wraps ``aiolimiter.AsyncLimiter`` behind context-manager factories
so callers can transparently enable / disable throttling depending
on the current ``LLMConfig`` flags.
"""

from __future__ import annotations

from typing import Union
from contextlib import nullcontext

from aiolimiter import AsyncLimiter
from m_flow.llm.config import get_llm_config as _fetch_cfg

# ---------------------------------------------------------------------------
# Module-private state
# ---------------------------------------------------------------------------

_llm_cfg = _fetch_cfg()

_llm_limiter: AsyncLimiter = AsyncLimiter(
    max_rate=_llm_cfg.llm_rate_limit_requests,
    time_period=_llm_cfg.embedding_rate_limit_interval,
)

_embed_limiter: AsyncLimiter = AsyncLimiter(
    max_rate=_llm_cfg.embedding_rate_limit_requests,
    time_period=_llm_cfg.embedding_rate_limit_interval,
)


# Public references for direct access
llm_rate_limiter = _llm_limiter
embedding_rate_limiter = _embed_limiter

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def _pick(
    enabled_flag: bool,
    limiter: AsyncLimiter,
) -> Union[AsyncLimiter, nullcontext]:
    """Return *limiter* when throttling is active, else a no-op context."""
    return limiter if enabled_flag else nullcontext()


def llm_rate_limiter_context_manager():
    """Yield the LLM rate limiter if throttling is on, else a passthrough."""
    return _pick(_llm_cfg.llm_rate_limit_enabled, _llm_limiter)


def embedding_rate_limiter_context_manager():
    """Yield the embedding rate limiter if throttling is on, else a passthrough."""
    return _pick(_llm_cfg.embedding_rate_limit_enabled, _embed_limiter)
