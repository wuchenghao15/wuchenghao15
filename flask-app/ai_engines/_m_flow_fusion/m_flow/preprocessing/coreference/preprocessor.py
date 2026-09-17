"""
Coreference preprocessing entry point.

Provides the main API for integrating coreference resolution into
mflow's search and retrieval pipeline.

Usage:
    from m_flow.preprocessing.coreference import preprocess_query_with_coref

    result = preprocess_query_with_coref(
        query="他去哪了？",
        user_id="user_123",
        session_id="session_abc",
    )
    print(result.resolved_query)  # "张三去哪了？"
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from m_flow.shared.logging_utils import get_logger

from .config import CorefConfig, get_coref_config
from .session_manager import SessionManager

__all__ = [
    "CorefResult",
    "preprocess_query_with_coref",
    "preprocess_query_with_coref_async",
    "reset_coref_session",
    "get_coref_stats",
    "clear_session_manager",
]

logger = get_logger("coref.preprocessor")


@dataclass
class CorefResult:
    """
    Result of coreference preprocessing.

    Attributes:
        original_query: The input query before processing.
        resolved_query: The query after coreference resolution.
        replacements: List of pronoun replacements made.
        session_id: Session ID used (if any).
        turn_count: Number of turns in the session.
    """

    original_query: str
    resolved_query: str
    replacements: List[Dict[str, Any]] = field(default_factory=list)
    session_id: Optional[str] = None
    turn_count: int = 0


# Global session manager singleton
_session_manager: Optional[SessionManager] = None
_manager_lock = threading.Lock()


def _get_session_manager() -> SessionManager:
    """
    Get global session manager singleton (thread-safe).

    Uses double-check locking pattern for efficient initialization.

    Returns:
        SessionManager instance.
    """
    global _session_manager
    if _session_manager is None:
        with _manager_lock:
            # Double-check inside lock
            if _session_manager is None:
                config = get_coref_config()
                _session_manager = SessionManager(
                    ttl_seconds=config.session_ttl,
                    max_history=config.max_history,
                    max_sessions=config.max_sessions,
                )
                logger.info(
                    f"Initialized SessionManager: max_history={config.max_history}, "
                    f"ttl={config.session_ttl}s, max_sessions={config.max_sessions}"
                )
    return _session_manager


def clear_session_manager() -> None:
    """
    Clear the session manager singleton.

    Call this after configuration changes to force reinitialization
    with new settings.
    """
    global _session_manager
    with _manager_lock:
        if _session_manager is not None:
            logger.info("Clearing session manager")
            _session_manager = None


def _detect_language(text: str) -> str:
    """
    Simple language detection.

    Args:
        text: Input text.

    Returns:
        "zh" for Chinese, "en" for English.
    """
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    total_alpha = sum(1 for c in text if c.isalpha())

    if total_alpha == 0:
        return "zh"

    return "zh" if chinese_chars / total_alpha > 0.3 else "en"


def _fallback_result(query: str, reason: str = "") -> CorefResult:
    """
    Create fallback result (original query unchanged).

    Args:
        query: Original query.
        reason: Optional reason for fallback (logged as warning).

    Returns:
        CorefResult with original query.
    """
    if reason:
        logger.warning(f"Coreference fallback: {reason}")
    return CorefResult(
        original_query=query,
        resolved_query=query,
        replacements=[],
        session_id=None,
        turn_count=0,
    )


def preprocess_query_with_coref(
    query: str,
    user_id: str,
    session_id: Optional[str] = None,
    enabled: Optional[bool] = None,
    new_turn: bool = True,
) -> CorefResult:
    """
    Preprocess query with coreference resolution.

    Resolves pronouns and anaphoric references in the query using
    session context from previous conversation turns.

    Args:
        query: Input query text.
        user_id: User identifier (required for session security).
        session_id: Session identifier. If None, defaults to f"user_{user_id}".
        enabled: Override global enabled setting. If None, uses config.
        new_turn: If True and paragraph_reset is enabled, resets partial context.

    Returns:
        CorefResult with resolved query and replacement details.

    Example:
        # First query establishes context
        r1 = preprocess_query_with_coref("张三去北京了。", "user1", "s1")

        # Second query resolves "他" to "张三"
        r2 = preprocess_query_with_coref("他在做什么？", "user1", "s1")
        print(r2.resolved_query)  # "张三在做什么？"
    """
    # Empty query: fast return
    if not query or not query.strip():
        return CorefResult(
            original_query=query,
            resolved_query=query,
            replacements=[],
            session_id=None,
            turn_count=0,
        )

    # Session ID length validation (prevent DoS)
    if session_id and len(session_id) > 128:
        return _fallback_result(
            query,
            f"session_id too long ({len(session_id)} > 128)",
        )

    # Get configuration
    try:
        config = get_coref_config()
    except Exception as e:
        return _fallback_result(query, f"config error: {e}")

    # Check if enabled
    is_enabled = enabled if enabled is not None else config.enabled
    if not is_enabled:
        return CorefResult(
            original_query=query,
            resolved_query=query,
            replacements=[],
            session_id=None,
            turn_count=0,
        )

    # Determine language
    if config.language == "auto":
        language = _detect_language(query)
    else:
        language = config.language

    # Resolve query
    try:
        manager = _get_session_manager()
        effective_session_id = session_id or f"user_{user_id}"

        resolved, replacements, turn_count = manager.resolve_query(
            session_id=effective_session_id,
            user_id=user_id,
            query=query,
            language=language,
            paragraph_reset=new_turn and config.paragraph_reset,
        )

        return CorefResult(
            original_query=query,
            resolved_query=resolved,
            replacements=replacements,
            session_id=effective_session_id,
            turn_count=turn_count,
        )

    except ImportError as e:
        return _fallback_result(query, f"module not installed: {e}")
    except Exception as e:
        return _fallback_result(query, f"resolution error: {e}")


async def preprocess_query_with_coref_async(
    query: str,
    user_id: str,
    session_id: Optional[str] = None,
    enabled: Optional[bool] = None,
    new_turn: bool = True,
) -> CorefResult:
    """
    Async version of preprocess_query_with_coref.

    Wraps the synchronous coreference resolution in a thread pool
    to avoid blocking the async event loop.

    Args:
        query: Input query text.
        user_id: User identifier.
        session_id: Session identifier.
        enabled: Override global enabled setting.
        new_turn: Reset partial context for new turn.

    Returns:
        CorefResult with resolved query.
    """
    from m_flow.shared.infra_utils.run_async import run_async

    return await run_async(
        preprocess_query_with_coref,
        query,
        user_id,
        session_id,
        enabled,
        new_turn,
    )


def reset_coref_session(session_id: str, user_id: Optional[str] = None) -> bool:
    """
    Reset a coreference session's context.

    Clears accumulated entity tracking and conversation history,
    allowing a fresh start without creating a new session.

    Args:
        session_id: Session identifier to reset.
        user_id: Optional user identifier for ownership validation.
                If provided, only resets if session belongs to this user.

    Returns:
        True if session was found and reset, False otherwise.
    """
    return _get_session_manager().reset_session(session_id, user_id)


def get_coref_stats(
    include_sessions: bool = False,
    limit: int = 100,
    filter_user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get coreference module statistics.

    Args:
        include_sessions: Include list of active sessions (may be large).
        limit: Maximum sessions to include.
        filter_user_id: If provided, only include sessions belonging to this user.
                       Use None for admin access to see all sessions.

    Returns:
        Statistics dictionary with:
            - active_sessions: Current session count (total or filtered)
            - max_sessions: Maximum allowed sessions
            - ttl_seconds: Session TTL
            - max_history: Entity history limit
            - sessions: (optional) Active session details
    """
    return _get_session_manager().get_stats(
        include_sessions=include_sessions,
        limit=limit,
        filter_user_id=filter_user_id,
    )
