"""
Pipeline run qualification check.

Determines if a dataset is eligible for a new pipeline run.
"""

from __future__ import annotations

from m_flow.data.models import Data, Dataset
from m_flow.pipeline.methods import get_pipeline_run_by_dataset
from m_flow.pipeline.models import RunStatus
from m_flow.pipeline.models.RunEvent import (
    RunCompleted,
    RunStarted,
)
from m_flow.pipeline.operations.get_workflow_status import get_workflow_status
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)


async def check_cache_status(
    dataset: Dataset,
    data: list[Data],
    workflow_name: str,
) -> RunStarted | RunCompleted | None:
    """
    Check whether a pipeline can be started for a dataset.

    Returns a status object if the dataset is already being processed
    or was previously processed; otherwise returns None to allow proceeding.

    Args:
        dataset: Target dataset.
        data: Data items to process.
        workflow_name: Name of the pipeline.

    Returns:
        - RunStarted if already in progress.
        - RunCompleted if already finished.
        - None if eligible for a new run.
    """
    if not isinstance(dataset, Dataset):
        return None

    statuses = await get_workflow_status([dataset.id], workflow_name)
    ds_key = str(dataset.id)

    if ds_key not in statuses:
        return None

    current = statuses[ds_key]

    if current == RunStatus.DATASET_PROCESSING_STARTED:
        _log.info("Dataset %s is already processing", dataset.id)
        run = await get_pipeline_run_by_dataset(dataset.id, workflow_name)
        return RunStarted(
            workflow_run_id=run.workflow_run_id,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            payload=data,
        )

    if current == RunStatus.DATASET_PROCESSING_COMPLETED:
        _log.info("Dataset %s already processed", dataset.id)
        run = await get_pipeline_run_by_dataset(dataset.id, workflow_name)
        return RunCompleted(
            workflow_run_id=run.workflow_run_id,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
        )

    return None
