"""
Activity Router
================

REST API endpoint for retrieving recent system activities.
Aggregates data from multiple sources (queries, pipeline_runs).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import Field

from m_flow.api.DTO import OutDTO

if TYPE_CHECKING:
    from m_flow.auth.models import User


# ---------------------------------------------------------------------------
# Response DTOs
# ---------------------------------------------------------------------------


class ActivityDTO(OutDTO):
    """Activity item for dashboard display."""

    id: str = Field(..., description="Activity unique identifier")
    type: str = Field(..., description="Activity type: search, ingest, create, delete, config")
    title: str = Field(..., description="Human-readable activity title")
    description: Optional[str] = Field(None, description="Activity description/details")
    status: str = Field(default="success", description="Activity status: success, error, pending")
    created_at: datetime = Field(..., description="When the activity occurred")


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


def get_activity_router() -> APIRouter:
    """
    Build and return the activity API router.

    Endpoints:
        GET / - Retrieve recent activities
    """
    router = APIRouter()

    @router.get("", response_model=List[ActivityDTO])
    async def list_activities(
        user: "User" = Depends(_auth_dep()),
        limit: int = Query(default=20, le=100, description="Maximum activities to return"),
    ):
        """
        Get recent activities aggregated from multiple sources.

        Activities are sourced from:
        - Search queries (queries table)
        - Ingest operations (pipeline_runs table)

        Returns activities sorted by creation time (newest first).
        """
        from m_flow.data.methods import get_recent_activities

        activities = await get_recent_activities(
            user_id=user.id,
            limit=limit,
        )

        return [
            ActivityDTO(
                id=a["id"],
                type=a["type"],
                title=a["title"],
                description=a["description"],
                status=a["status"],
                created_at=a["created_at"],
            )
            for a in activities
        ]

    return router
