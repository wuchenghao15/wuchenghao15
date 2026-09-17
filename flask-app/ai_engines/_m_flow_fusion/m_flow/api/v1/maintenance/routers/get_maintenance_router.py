"""
Maintenance API Router.

Provides endpoints for Episode quality checking and fixing.
Uses the same safety patterns as the prune router.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from m_flow.api.v1.maintenance.episode_quality import (
    get_episode_quality_stats,
    run_size_check_for_episodes,
)
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User

_logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------


def _get_auth_user():
    """Return the authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# -----------------------------------------------------------------------------
# Safety Check (uses get_active_pipeline_runs for consistency)
# -----------------------------------------------------------------------------


async def _check_no_running_pipelines() -> None:
    """
    Verify no pipelines are currently running.

    Uses get_active_pipeline_runs() which correctly handles:
    - Deterministic run_ids (same id for multiple runs)
    - ROW_NUMBER window function to get latest status per (dataset_id, workflow_name)
    - Both STARTED and INITIATED states

    Raises HTTPException 409 if active pipelines found.
    """
    from m_flow.pipeline.methods import get_active_pipeline_runs

    try:
        running = await get_active_pipeline_runs()

        if running:
            details = [f"{r['workflow_name']}({r['status']})" for r in running[:5]]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot run Size Check while pipelines are active. "
                    f"Found {len(running)} active pipeline(s): {', '.join(details)}"
                ),
            )
    except HTTPException:
        raise
    except Exception as e:
        _logger.warning(f"[maintenance] Could not verify pipeline status: {e}")


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------


class SizeCheckRequest(BaseModel):
    """Request body for episode size check."""

    episode_ids: List[str] = Field(..., min_length=1, description="List of Episode IDs to check")


class SizeCheckResult(BaseModel):
    """Single episode size check result."""

    episode_id: str
    episode_name: Optional[str] = None
    decision: str  # "SPLIT" | "KEEP" | "ERROR" | "SKIPPED"
    reasoning: Optional[str] = None
    new_episodes: Optional[List[dict]] = None
    adapted_threshold: Optional[int] = None


class SizeCheckSummary(BaseModel):
    """Summary of size check results."""

    checked: int
    split: int
    kept: int
    skipped: int
    errors: int


class SizeCheckResponse(BaseModel):
    """Response for episode size check."""

    results: List[SizeCheckResult]
    summary: SizeCheckSummary


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------


def get_maintenance_router() -> APIRouter:
    """Create maintenance API router."""
    router = APIRouter()

    @router.get("/episode-quality")
    async def get_quality_stats(
        dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Get Episode quality statistics.

        Returns all Episodes with quality metrics:
        - Empty Episodes (facet_count = 0)
        - Oversized Episodes (facet_count > threshold)

        This is a read-only operation, safe to call anytime.
        """
        from uuid import UUID

        from m_flow.auth.permissions.methods import get_all_user_permission_datasets
        from m_flow.context_global_variables import (
            backend_access_control_enabled,
            set_db_context,
        )

        try:
            if dataset_id and backend_access_control_enabled():
                try:
                    ds_uuid = UUID(dataset_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid dataset_id format: {dataset_id}",
                    )
                all_datasets = await get_all_user_permission_datasets(user, "read")
                authorized = next((ds for ds in all_datasets if ds.id == ds_uuid), None)
                if not authorized:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Dataset {dataset_id} not found or not accessible",
                    )
                await set_db_context(ds_uuid, authorized.owner_id)

            return await get_episode_quality_stats(dataset_id)
        except HTTPException:
            raise
        except Exception as e:
            _logger.error(f"[maintenance] Failed to get quality stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get Episode quality stats: {str(e)}",
            )

    @router.post("/episode-size-check", response_model=SizeCheckResponse)
    async def run_size_check(
        request: SizeCheckRequest,
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Run Size Check on specified Episodes.

        Safety checks:
        1. Verifies no pipelines are actively running
        2. Filters out Episodes with 0 facets

        For each Episode, uses LLM to determine if it should be:
        - SPLIT: Multiple semantic foci detected, Episode will be split
        - KEEP: Single coherent focus, threshold will be adapted
        """
        # Safety check: no running pipelines
        await _check_no_running_pipelines()

        _logger.info(
            f"[maintenance] Size Check requested for {len(request.episode_ids)} episodes "
            f"by user {user.email if user else 'unknown'}"
        )

        try:
            result = await run_size_check_for_episodes(request.episode_ids)

            _logger.info(
                f"[maintenance] Size Check completed: "
                f"checked={result['summary']['checked']}, "
                f"split={result['summary']['split']}, "
                f"kept={result['summary']['kept']}"
            )

            return result
        except Exception as e:
            _logger.error(f"[maintenance] Size Check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Size Check failed: {str(e)}",
            )

    return router
