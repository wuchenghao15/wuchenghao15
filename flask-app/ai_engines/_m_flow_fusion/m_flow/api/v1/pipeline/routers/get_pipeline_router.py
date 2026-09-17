"""
Pipeline Router
================

REST API endpoint for pipeline operations.
Currently provides active pipeline status for real-time progress tracking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from pydantic import Field

from m_flow.api.DTO import OutDTO

if TYPE_CHECKING:
    from m_flow.auth.models import User


class ActivePipelineDTO(OutDTO):
    """Active pipeline information for dashboard display."""

    workflow_run_id: str = Field(..., description="Pipeline run unique identifier")
    dataset_id: Optional[str] = Field(None, description="Target dataset ID")
    dataset_name: Optional[str] = Field(None, description="Target dataset name for matching")
    workflow_name: str = Field(..., description="Pipeline name identifier")
    status: str = Field(..., description="Pipeline status")
    total_items: Optional[int] = Field(None, description="Total items to process")
    processed_items: Optional[int] = Field(None, description="Items processed so far")
    current_step: Optional[str] = Field(None, description="Current task being executed")
    started_at: Optional[str] = Field(None, description="When progress tracking started")
    updated_at: Optional[str] = Field(None, description="Last progress update timestamp")
    created_at: Optional[str] = Field(None, description="Pipeline run creation time")


class DismissResponseDTO(OutDTO):
    """Response for dismiss operation."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Result message")


def _auth_dep():
    """Return the authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


def get_pipeline_router() -> APIRouter:
    """
    Build and return the pipeline API router.

    Endpoints:
        GET /active - Get currently active pipeline runs
        DELETE /active/{workflow_run_id} - Dismiss a stale pipeline
    """
    router = APIRouter()

    @router.get("/active", response_model=List[ActivePipelineDTO])
    async def get_active_pipelines(
        user: "User" = Depends(_auth_dep()),
    ):
        """
        Get all currently active (running) pipeline operations.

        Returns pipelines that are in STARTED status and have not
        completed or errored. Includes real-time progress info.
        """
        from m_flow.pipeline.methods import get_active_pipeline_runs

        pipelines = await get_active_pipeline_runs()

        return [ActivePipelineDTO(**p) for p in pipelines]

    @router.delete("/active/{workflow_run_id}", response_model=DismissResponseDTO)
    async def dismiss_stale_pipeline(
        workflow_run_id: UUID = Path(..., description="Pipeline run ID to dismiss"),
        user: "User" = Depends(_auth_dep()),
    ):
        """
        Dismiss a stale pipeline by marking it as errored.

        This is used to clean up pipelines that appear stuck or orphaned.
        Creates an ERRORED record so the pipeline no longer shows as active.
        """
        from m_flow.pipeline.methods import dismiss_pipeline_run

        result = await dismiss_pipeline_run(workflow_run_id)

        return DismissResponseDTO(
            success=result["success"],
            message=result["message"],
        )

    return router
