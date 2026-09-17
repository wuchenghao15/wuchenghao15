"""
Reset pipeline run status.

Forces a dataset to be re-eligible for pipeline processing.
"""

from __future__ import annotations

from uuid import UUID

from m_flow.pipeline.operations.record_run_initiated import record_run_initiated
from m_flow.pipeline.utils.derive_pipeline_key import derive_pipeline_key


async def reset_pipeline_run_status(
    user_id: UUID,
    dataset_id: UUID,
    workflow_name: str,
) -> None:
    """
    Reset the run status for a dataset so it can be re-processed.

    This re-initializes the pipeline run record, allowing the dataset
    to be picked up again instead of being skipped as already completed.

    Args:
        user_id: Owner of the dataset.
        dataset_id: Target dataset.
        workflow_name: Pipeline to reset.
    """
    pid = derive_pipeline_key(user_id, dataset_id, workflow_name)

    await record_run_initiated(
        workflow_id=pid,
        workflow_name=workflow_name,
        dataset_id=dataset_id,
    )
