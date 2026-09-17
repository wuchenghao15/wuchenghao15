"""
Coreference Resolution API Router.

Provides endpoints for:
- Configuration management (GET/POST /settings/coreference)
- Statistics monitoring (GET /coreference/stats)
- Session management (POST /coreference/sessions/{id}/reset)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from m_flow.auth.models import User


# ---------------------------------------------------------------------------
# Request/Response DTOs
# ---------------------------------------------------------------------------


class CorefConfigResponse(BaseModel):
    """Coreference configuration response."""

    enabled: bool
    max_history: int
    session_ttl: int
    max_sessions: int
    language: Literal["auto", "zh", "en"]
    paragraph_reset: bool


class CorefConfigUpdate(BaseModel):
    """Coreference configuration update request."""

    enabled: Optional[bool] = None
    max_history: Optional[int] = Field(None, ge=5, le=50)
    session_ttl: Optional[int] = Field(None, ge=60, le=86400)
    max_sessions: Optional[int] = Field(None, ge=100, le=100000)
    language: Optional[Literal["auto", "zh", "en"]] = None
    paragraph_reset: Optional[bool] = None


class SessionInfo(BaseModel):
    """Session information."""

    session_id: str
    user_id: str
    turn_count: int
    last_active: str
    language: str


class CorefStatsResponse(BaseModel):
    """Coreference statistics response."""

    active_sessions: int
    max_sessions: int
    ttl_seconds: int
    max_history: int
    sessions: Optional[list[SessionInfo]] = None


class ResetResponse(BaseModel):
    """Session reset response."""

    status: str
    session_id: str


class ConfigUpdateResponse(BaseModel):
    """Configuration update response."""

    status: str
    message: str


# ---------------------------------------------------------------------------
# Authentication Dependency
# ---------------------------------------------------------------------------


def _auth_dep():
    """Return the authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def get_coreference_router() -> APIRouter:
    """
    Build and return the coreference API router.

    Endpoints:
        GET  /settings/coreference      - Get current configuration
        POST /settings/coreference      - Update configuration
        GET  /coreference/stats         - Get session statistics
        POST /coreference/sessions/{id}/reset - Reset a session
    """
    router = APIRouter()

    @router.get(
        "/settings/coreference",
        response_model=CorefConfigResponse,
        tags=["settings"],
    )
    async def get_coreference_config(user: "User" = Depends(_auth_dep())):
        """
        Get current coreference configuration.

        Returns the active configuration including enabled state,
        history limits, session TTL, and language settings.
        """
        try:
            from m_flow.preprocessing.coreference import get_coref_config

            config = get_coref_config()
            return CorefConfigResponse(
                enabled=config.enabled,
                max_history=config.max_history,
                session_ttl=config.session_ttl,
                max_sessions=config.max_sessions,
                language=config.language,
                paragraph_reset=config.paragraph_reset,
            )
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Coreference module not available: {e}",
            )

    @router.post(
        "/settings/coreference",
        response_model=ConfigUpdateResponse,
        tags=["settings"],
    )
    async def update_coreference_config(
        update: CorefConfigUpdate,
        user: "User" = Depends(_auth_dep()),
    ):
        """
        Update coreference configuration.

        Changes are applied by setting environment variables and
        clearing configuration caches. The session manager is also
        reset to apply new settings.

        Note: Changes persist only for the current process lifecycle.
        For persistent changes, update the environment directly.
        """
        from m_flow.config.presets import clear_config_caches

        # Apply updates to environment
        if update.enabled is not None:
            os.environ["MFLOW_COREF_ENABLED"] = str(update.enabled).lower()
        if update.max_history is not None:
            os.environ["MFLOW_COREF_MAX_HISTORY"] = str(update.max_history)
        if update.session_ttl is not None:
            os.environ["MFLOW_COREF_SESSION_TTL"] = str(update.session_ttl)
        if update.max_sessions is not None:
            os.environ["MFLOW_COREF_MAX_SESSIONS"] = str(update.max_sessions)
        if update.language is not None:
            os.environ["MFLOW_COREF_LANGUAGE"] = update.language
        if update.paragraph_reset is not None:
            os.environ["MFLOW_COREF_PARAGRAPH_RESET"] = str(update.paragraph_reset).lower()

        # Clear caches to reload configuration
        clear_config_caches()

        return ConfigUpdateResponse(
            status="ok",
            message="Configuration updated successfully",
        )

    @router.get(
        "/coreference/stats",
        response_model=CorefStatsResponse,
        tags=["coreference"],
    )
    async def get_coreference_stats(
        include_sessions: bool = False,
        limit: int = 100,
        user: "User" = Depends(_auth_dep()),
    ):
        """
        Get coreference module statistics.

        Returns active session count, configuration limits, and
        optionally a list of active sessions (filtered to current user only
        for privacy protection).

        Args:
            include_sessions: Include list of active sessions.
            limit: Maximum sessions to include (default: 100).
        """
        try:
            from m_flow.preprocessing.coreference import get_coref_stats

            # Filter sessions to current user for privacy
            stats = get_coref_stats(
                include_sessions=include_sessions,
                limit=limit,
                filter_user_id=str(user.id),
            )

            response = CorefStatsResponse(
                active_sessions=stats["active_sessions"],
                max_sessions=stats["max_sessions"],
                ttl_seconds=stats["ttl_seconds"],
                max_history=stats["max_history"],
            )

            if include_sessions and "sessions" in stats:
                response.sessions = [SessionInfo(**s) for s in stats["sessions"]]

            return response
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Coreference module not available: {e}",
            )

    @router.post(
        "/coreference/sessions/{session_id}/reset",
        response_model=ResetResponse,
        tags=["coreference"],
    )
    async def reset_coreference_session(
        session_id: str,
        user: "User" = Depends(_auth_dep()),
    ):
        """
        Reset a coreference session's context.

        Clears accumulated entity tracking for the specified session,
        allowing a fresh start without creating a new session.

        Note: Only the session owner can reset their own session.
        """
        try:
            from m_flow.preprocessing.coreference import reset_coref_session

            # Pass user_id for ownership validation
            success = reset_coref_session(session_id, user_id=str(user.id))
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session not found or access denied: {session_id}",
                )

            return ResetResponse(status="ok", session_id=session_id)
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Coreference module not available: {e}",
            )

    return router
