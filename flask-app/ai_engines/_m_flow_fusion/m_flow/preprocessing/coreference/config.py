"""
Coreference resolution configuration.

Controls behavior of the coreference preprocessing module including
session management, history limits, and language settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Literal

from m_flow.config.env_registry import get_env
from m_flow.shared.logging_utils import get_logger

__all__ = ["CorefConfig", "get_coref_config"]

logger = get_logger("coref.config")


@dataclass
class CorefConfig:
    """
    Coreference resolution configuration.

    Attributes:
        enabled: Enable/disable coreference preprocessing globally.
        max_history: Maximum number of historical entities to track (5-50).
                    Higher values improve accuracy but use more memory.
        session_ttl: Session time-to-live in seconds (60-86400).
                    Inactive sessions are cleaned up after this duration.
        max_sessions: Maximum number of concurrent sessions (100-100000).
                     Oldest sessions are evicted when limit is reached.
        language: Language mode - "auto" (detect), "zh" (Chinese), or "en" (English).
        paragraph_reset: Reset partial context on new conversation turns.
    """

    enabled: bool = True
    max_history: int = 10
    session_ttl: int = 3600
    max_sessions: int = 10000
    language: Literal["auto", "zh", "en"] = "auto"
    paragraph_reset: bool = True

    def __post_init__(self) -> None:
        """Validate and clamp configuration parameters."""
        original_values = {
            "max_history": self.max_history,
            "session_ttl": self.session_ttl,
            "max_sessions": self.max_sessions,
            "language": self.language,
        }

        # max_history: 5-50
        if self.max_history < 5:
            self.max_history = 5
        elif self.max_history > 50:
            self.max_history = 50

        # session_ttl: 60-86400 (1 minute to 24 hours)
        if self.session_ttl < 60:
            self.session_ttl = 60
        elif self.session_ttl > 86400:
            self.session_ttl = 86400

        # max_sessions: 100-100000
        if self.max_sessions < 100:
            self.max_sessions = 100
        elif self.max_sessions > 100000:
            self.max_sessions = 100000

        # language: must be one of "auto", "zh", "en"
        if self.language not in ("auto", "zh", "en"):
            logger.warning(f"Invalid language '{self.language}', defaulting to 'auto'")
            self.language = "auto"

        # Log any clamped values
        clamped = {
            k: (original_values[k], getattr(self, k)) for k in original_values if original_values[k] != getattr(self, k)
        }
        if clamped:
            logger.warning(f"Config values clamped: {clamped}")


@lru_cache(maxsize=1)
def get_coref_config() -> CorefConfig:
    """
    Get coreference configuration from environment variables.

    Configuration is cached after first call. Call clear_config_caches()
    to reload after environment changes.

    Environment Variables:
        MFLOW_COREF_ENABLED: Enable coreference preprocessing (default: true)
        MFLOW_COREF_MAX_HISTORY: Entity history limit, 5-50 (default: 10)
        MFLOW_COREF_SESSION_TTL: Session TTL in seconds, 60-86400 (default: 3600)
        MFLOW_COREF_MAX_SESSIONS: Max concurrent sessions, 100-100000 (default: 10000)
        MFLOW_COREF_LANGUAGE: Language mode: auto|zh|en (default: auto)
        MFLOW_COREF_PARAGRAPH_RESET: Reset context on new turns (default: true)

    Returns:
        CorefConfig instance with validated parameters.
    """
    return CorefConfig(
        enabled=get_env("MFLOW_COREF_ENABLED", True),
        max_history=get_env("MFLOW_COREF_MAX_HISTORY", 10),
        session_ttl=get_env("MFLOW_COREF_SESSION_TTL", 3600),
        max_sessions=get_env("MFLOW_COREF_MAX_SESSIONS", 10000),
        language=get_env("MFLOW_COREF_LANGUAGE", "auto"),
        paragraph_reset=get_env("MFLOW_COREF_PARAGRAPH_RESET", True),
    )
