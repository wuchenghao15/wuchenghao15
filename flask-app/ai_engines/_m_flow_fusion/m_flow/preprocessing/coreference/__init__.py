"""
Coreference Resolution Preprocessing Module.

Provides query preprocessing with coreference resolution for
improved retrieval accuracy. Supports streaming resolution with
session context accumulation.

Features:
    - Chinese and English coreference resolution
    - Session-based context tracking
    - Thread-safe multi-user support
    - LRU session eviction
    - Configurable history limits

Usage:
    from m_flow.preprocessing.coreference import (
        preprocess_query_with_coref,
        get_coref_config,
    )

    # Single query
    result = preprocess_query_with_coref(
        query="他去哪了？",
        user_id="user_123",
    )
    print(result.resolved_query)

    # Check configuration
    config = get_coref_config()
    print(f"Enabled: {config.enabled}")
"""

from .config import CorefConfig, get_coref_config
from .preprocessor import (
    CorefResult,
    preprocess_query_with_coref,
    preprocess_query_with_coref_async,
    reset_coref_session,
    get_coref_stats,
    clear_session_manager,
)

__all__ = [
    # Configuration
    "CorefConfig",
    "get_coref_config",
    # Preprocessing
    "CorefResult",
    "preprocess_query_with_coref",
    "preprocess_query_with_coref_async",
    "reset_coref_session",
    "get_coref_stats",
    "clear_session_manager",
]
