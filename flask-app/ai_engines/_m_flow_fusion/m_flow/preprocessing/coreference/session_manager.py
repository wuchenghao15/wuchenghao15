"""
Coreference session management.

Manages multi-user coreference resolution sessions with LRU eviction,
TTL expiration, and thread-safe operations.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from m_flow.shared.logging_utils import get_logger

__all__ = ["SessionManager", "CorefSession"]

logger = get_logger("coref.session")


@dataclass
class CorefSession:
    """
    A single user's coreference resolution session.

    Maintains state for streaming coreference resolution across
    multiple conversation turns.

    Attributes:
        session_id: Unique session identifier.
        user_id: User identifier for security validation.
        stream_session: The underlying StreamCorefSession from coreference module.
        created_at: Session creation timestamp.
        last_active: Last activity timestamp (updated on each query).
        turn_count: Number of queries processed in this session.
        language: Current language mode for this session.
    """

    session_id: str
    user_id: str
    stream_session: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    turn_count: int = 0
    language: str = "zh"

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if session has expired based on TTL."""
        age = (datetime.now() - self.last_active).total_seconds()
        return age > ttl_seconds


class SessionManager:
    """
    Thread-safe coreference session manager.

    Features:
        - LRU eviction when max_sessions is reached
        - TTL-based expiration of inactive sessions
        - Thread-safe operations with RLock
        - User ID validation to prevent cross-user session access
        - Support for both Chinese and English coreference modules

    Usage:
        manager = SessionManager(ttl_seconds=3600, max_history=20, max_sessions=10000)
        resolved, replacements, turn_count = manager.resolve_query(
            session_id="user_123",
            user_id="user_123",
            query="他去哪了？",
            language="zh"
        )
    """

    def __init__(
        self,
        ttl_seconds: int = 3600,
        max_history: int = 10,
        max_sessions: int = 10000,
    ) -> None:
        """
        Initialize session manager.

        Args:
            ttl_seconds: Session time-to-live in seconds.
            max_history: Max historical entities per session.
            max_sessions: Maximum concurrent sessions (LRU eviction).
        """
        self._ttl = ttl_seconds
        self._max_history = max_history
        self._max_sessions = max_sessions
        self._sessions: Dict[str, CorefSession] = {}
        self._session_order: List[str] = []  # LRU tracking
        self._lock = threading.RLock()

    def get_or_create(
        self,
        session_id: str,
        user_id: str,
        language: str = "zh",
    ) -> CorefSession:
        """
        Get existing session or create new one (thread-safe).

        Args:
            session_id: Session identifier.
            user_id: User identifier for security validation.
            language: Language mode ("zh" or "en").

        Returns:
            CorefSession instance.

        Note:
            If session exists but user_id doesn't match, the old session
            is deleted and a new one is created (security measure).
        """
        with self._lock:
            return self._get_or_create_unlocked(session_id, user_id, language)

    def _get_or_create_unlocked(
        self,
        session_id: str,
        user_id: str,
        language: str = "zh",
    ) -> CorefSession:
        """
        Internal method to get/create session. Must be called with lock held.

        Args:
            session_id: Session identifier.
            user_id: User identifier.
            language: Language mode.

        Returns:
            CorefSession instance.
        """
        # Cleanup expired and enforce limits
        self._cleanup_expired()
        self._enforce_max_sessions()

        # Check existing session
        if session_id in self._sessions:
            session = self._sessions[session_id]

            # Security: Verify user_id matches
            if session.user_id != user_id:
                logger.warning(
                    f"Session {session_id[:8]}... user_id mismatch: "
                    f"expected {session.user_id[:8]}..., got {user_id[:8]}..."
                )
                # Security: Delete mismatched session, create new
                del self._sessions[session_id]
                if session_id in self._session_order:
                    self._session_order.remove(session_id)
                # Fall through to create new session
            else:
                # Update LRU order
                session.last_active = datetime.now()
                if session_id in self._session_order:
                    self._session_order.remove(session_id)
                self._session_order.append(session_id)

                # Handle language change
                if session.language != language:
                    logger.debug(
                        f"Session {session_id[:8]}... language changed "
                        f"{session.language} -> {language}, resetting context"
                    )
                    session.stream_session.reset()
                    session.language = language

                return session

        # Create new session with appropriate language module
        stream_session = self._create_stream_session(language)

        session = CorefSession(
            session_id=session_id,
            user_id=user_id,
            stream_session=stream_session,
            language=language,
        )
        self._sessions[session_id] = session
        self._session_order.append(session_id)

        logger.debug(f"Created session {session_id[:8]}... (lang={language}, total={len(self._sessions)})")
        return session

    def _create_stream_session(self, language: str) -> Any:
        """
        Create a StreamCorefSession for the specified language.

        Args:
            language: "zh" for Chinese, "en" for English.

        Returns:
            StreamCorefSession instance.

        Raises:
            ImportError: If coreference module is not installed.
        """
        if language == "en":
            from english_coreference import (
                CoreferenceResolver as EnResolver,
                StreamCorefSession as EnStreamSession,
            )

            resolver = EnResolver(max_history=self._max_history)
            return EnStreamSession(resolver)
        else:
            from coreference_module import (
                CoreferenceResolver,
                StreamCorefSession,
            )

            resolver = CoreferenceResolver(max_history=self._max_history)
            return StreamCorefSession(resolver)

    def resolve_query(
        self,
        session_id: str,
        user_id: str,
        query: str,
        language: str = "zh",
        paragraph_reset: bool = False,
    ) -> Tuple[str, List[Dict], int]:
        """
        Resolve coreferences in query using session context (thread-safe).

        The entire resolution process is locked to prevent concurrent
        access to the same session's state.

        Args:
            session_id: Session identifier.
            user_id: User identifier for validation.
            query: Input text to resolve.
            language: Language mode ("zh" or "en").
            paragraph_reset: Reset partial context for new turn.

        Returns:
            Tuple of (resolved_text, replacements, turn_count).
        """
        with self._lock:
            session = self._get_or_create_unlocked(session_id, user_id, language)

            # Perform resolution
            resolved, replacements = session.stream_session.add_sentence(
                query,
                paragraph_reset=paragraph_reset,
            )
            session.turn_count += 1
            session.last_active = datetime.now()

            # Convert replacements to dict format if needed
            replacement_dicts = []
            for r in replacements:
                if hasattr(r, "__dict__"):
                    replacement_dicts.append(vars(r))
                elif isinstance(r, dict):
                    replacement_dicts.append(r)
                else:
                    replacement_dicts.append({"replacement": str(r)})

            return resolved, replacement_dicts, session.turn_count

    def reset_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """
        Reset a session's coreference context.

        Args:
            session_id: Session identifier.
            user_id: Optional user identifier for ownership validation.
                    If provided, only resets if session belongs to this user.

        Returns:
            True if session was found and reset, False otherwise.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                # Security: Verify ownership if user_id provided
                if user_id is not None and session.user_id != user_id:
                    logger.warning(f"Reset denied for session {session_id[:8]}...: user_id mismatch")
                    return False

                session.stream_session.reset()
                session.turn_count = 0
                session.last_active = datetime.now()
                logger.debug(f"Reset session {session_id[:8]}...")
                return True
            return False

    def _cleanup_expired(self) -> int:
        """
        Remove expired sessions. Must be called with lock held.

        Returns:
            Number of sessions removed.
        """
        expired = [sid for sid, session in self._sessions.items() if session.is_expired(self._ttl)]
        for sid in expired:
            del self._sessions[sid]
            if sid in self._session_order:
                self._session_order.remove(sid)

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)

    def _enforce_max_sessions(self) -> int:
        """
        Evict oldest sessions if limit exceeded. Must be called with lock held.

        Uses LRU order from _session_order list.

        Returns:
            Number of sessions evicted.
        """
        evicted = 0
        while len(self._sessions) >= self._max_sessions and self._session_order:
            oldest_id = self._session_order.pop(0)
            if oldest_id in self._sessions:
                del self._sessions[oldest_id]
                evicted += 1

        if evicted:
            logger.debug(f"Evicted {evicted} sessions (LRU)")
        return evicted

    def get_stats(
        self,
        include_sessions: bool = False,
        limit: int = 100,
        filter_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get session manager statistics.

        Args:
            include_sessions: Include list of active sessions.
            limit: Maximum number of sessions to include if include_sessions=True.
            filter_user_id: If provided, only include sessions belonging to this user.
                           Use None to include all sessions (admin access).

        Returns:
            Statistics dictionary with keys:
                - active_sessions: Current session count (total or filtered)
                - max_sessions: Maximum allowed sessions
                - ttl_seconds: Session TTL
                - max_history: Entity history limit
                - sessions: (optional) List of session info dicts
        """
        with self._lock:
            # Filter sessions by user if specified
            if filter_user_id is not None:
                filtered_sessions = {sid: s for sid, s in self._sessions.items() if s.user_id == filter_user_id}
                active_count = len(filtered_sessions)
            else:
                filtered_sessions = self._sessions
                active_count = len(self._sessions)

            stats = {
                "active_sessions": active_count,
                "max_sessions": self._max_sessions,
                "ttl_seconds": self._ttl,
                "max_history": self._max_history,
            }

            if include_sessions:
                sessions_list = []
                for i, (sid, session) in enumerate(filtered_sessions.items()):
                    if i >= limit:
                        break
                    sessions_list.append(
                        {
                            "session_id": sid,
                            "user_id": session.user_id[:8] + "...",  # Truncate for privacy
                            "turn_count": session.turn_count,
                            "last_active": session.last_active.isoformat(),
                            "language": session.language,
                        }
                    )
                stats["sessions"] = sessions_list

            return stats
