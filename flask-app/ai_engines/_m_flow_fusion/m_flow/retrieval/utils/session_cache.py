"""
Session-based conversation caching for M-flow.

Provides functions to persist and retrieve conversation history
using the configured cache backend.
"""

from __future__ import annotations

from typing import Optional

from m_flow.adapters.cache.config import CacheConfig
from m_flow.adapters.exceptions import CacheConnectionError
from m_flow.context_global_variables import session_user
from m_flow.shared.logging_utils import get_logger

_log = get_logger("session_cache")

_DEFAULT_SESSION = "default_session"


def _get_current_user_id() -> Optional[str]:
    """Extract the current user ID from session context."""
    user = session_user.get()
    uid = getattr(user, "id", None)
    return str(uid) if uid else None


def _is_caching_enabled() -> bool:
    """Check if caching is enabled in configuration."""
    try:
        config = CacheConfig()
        return bool(config.caching)
    except Exception:
        return False


async def _get_cache():
    """Lazily import and return the cache engine."""
    from m_flow.adapters.cache.get_cache_engine import get_cache_engine

    return get_cache_engine()


async def save_conversation_history(
    query: str,
    context_summary: str,
    answer: str,
    session_id: Optional[str] = None,
) -> bool:
    """
    Persist a Q&A exchange to the session cache.

    Requires an authenticated user and enabled caching.
    Fails silently if cache is unavailable.

    Args:
        query: User's question.
        context_summary: Context used to generate the answer.
        answer: Generated response.
        session_id: Session identifier (defaults to 'default_session').

    Returns:
        True if saved successfully, False otherwise.
    """
    user_id = _get_current_user_id()
    if not user_id or not _is_caching_enabled():
        _log.debug("Cache save skipped: user=%s, caching=%s", user_id, _is_caching_enabled())
        return False

    sid = session_id or _DEFAULT_SESSION

    try:
        cache = await _get_cache()
        if cache is None:
            _log.warning("Cache engine unavailable")
            return False

        await cache.add_qa(
            user_id,
            session_id=sid,
            question=query,
            context=context_summary,
            answer=answer,
        )

        _log.info("Q&A saved to cache: user=%s, session=%s", user_id, sid)
        return True

    except CacheConnectionError as err:
        _log.warning("Cache connection failed: %s", err.message)
        return False

    except Exception as err:
        _log.error("Unexpected cache error: %s: %s", type(err).__name__, err)
        return False


def _format_history_entry(entry: dict) -> str:
    """Format a single history entry as text."""
    lines = [
        f"[{entry.get('time', 'Unknown')}]",
        f"QUESTION: {entry.get('question', '')}",
        f"CONTEXT: {entry.get('context', '')}",
        f"ANSWER: {entry.get('answer', '')}",
    ]
    return "\n".join(lines)


async def get_conversation_history(
    session_id: Optional[str] = None,
) -> str:
    """
    Retrieve formatted conversation history from cache.

    Returns Q&A history formatted with timestamps for
    use in context-aware responses.

    Args:
        session_id: Session identifier (defaults to 'default_session').

    Returns:
        Formatted history string, or empty string if unavailable.
    """
    user_id = _get_current_user_id()
    if not user_id or not _is_caching_enabled():
        _log.debug("History retrieval skipped: no user or caching disabled")
        return ""

    sid = session_id or _DEFAULT_SESSION

    try:
        cache = await _get_cache()
        if cache is None:
            _log.warning("Cache engine unavailable for history retrieval")
            return ""

        entries = await cache.get_latest_qa(user_id, sid)

        if not entries:
            _log.debug("No conversation history found")
            return ""

        header = "Previous conversation:\n\n"
        formatted = "\n\n".join(_format_history_entry(e) for e in entries)

        _log.debug("Retrieved %d history entries", len(entries))
        return header + formatted + "\n"

    except CacheConnectionError as err:
        _log.warning("Cache connection failed for history: %s", err.message)
        return ""

    except Exception as err:
        _log.warning("History retrieval error: %s: %s", type(err).__name__, err)
        return ""
