"""
Global LLM Concurrency Control

Provides a unified semaphore for all LLM calls across episodic and procedural pipelines.
This ensures natural competition for LLM resources without nested semaphore issues.
"""

import asyncio
import os
from typing import Optional

_GLOBAL_SEMAPHORE: Optional[asyncio.Semaphore] = None


def get_global_llm_semaphore() -> asyncio.Semaphore:
    """
    Get or create the global LLM concurrency semaphore.

    Limit is controlled by MFLOW_LLM_CONCURRENCY_LIMIT environment variable.
    Default: 20

    Returns:
        asyncio.Semaphore for controlling concurrent LLM calls
    """
    global _GLOBAL_SEMAPHORE
    if _GLOBAL_SEMAPHORE is None:
        limit = int(os.getenv("MFLOW_LLM_CONCURRENCY_LIMIT", "20"))
        _GLOBAL_SEMAPHORE = asyncio.Semaphore(limit)
    return _GLOBAL_SEMAPHORE


def reset_global_llm_semaphore() -> None:
    """Reset the global semaphore (for testing purposes)."""
    global _GLOBAL_SEMAPHORE
    _GLOBAL_SEMAPHORE = None


def get_llm_concurrency_limit() -> int:
    """
    Get the configured LLM concurrency limit value.

    Returns:
        int: The concurrency limit from MFLOW_LLM_CONCURRENCY_LIMIT env var, default 20
    """
    return int(os.getenv("MFLOW_LLM_CONCURRENCY_LIMIT", "20"))
