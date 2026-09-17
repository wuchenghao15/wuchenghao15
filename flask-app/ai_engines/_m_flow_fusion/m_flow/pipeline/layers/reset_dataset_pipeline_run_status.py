"""
Pipeline run status reset.

Resets pipeline status for dataset reprocessing.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from m_flow.auth.models import User
from m_flow.pipeline.methods import get_pipeline_runs_by_dataset, reset_pipeline_run_status
from m_flow.pipeline.models.PipelineRun import RunStatus


async def reset_dataset_pipeline_run_status(
    dataset_id: UUID,
    user: User,
    pipeline_names: Optional[list[str]] = None,
) -> None:
    """
    Reset pipeline run statuses for dataset.

    Allows reprocessing of data through pipelines.

    Args:
        dataset_id: Target dataset.
        user: Requesting user.
        pipeline_names: Filter to specific pipelines (optional).
    """
    runs = await get_pipeline_runs_by_dataset(dataset_id)

    for run in runs:
        # Skip initiated runs
        if run.status == RunStatus.DATASET_PROCESSING_INITIATED:
            continue

        # Apply name filter if provided
        if pipeline_names and run.workflow_name not in pipeline_names:
            continue

        await reset_pipeline_run_status(
            user.id,
            dataset_id,
            run.workflow_name,
        )
