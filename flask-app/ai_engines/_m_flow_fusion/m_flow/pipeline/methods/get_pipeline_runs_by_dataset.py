"""Retrieve the latest pipeline execution for every pipeline tied to a dataset."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from m_flow.adapters.relational import get_db_adapter
from ..models import WorkflowRun

_logger = logging.getLogger(__name__)


async def get_pipeline_runs_by_dataset(dataset_id: UUID) -> list[WorkflowRun]:
    """Return the most recent run of each pipeline for *dataset_id*.

    Constructs a window function that partitions runs by
    ``(dataset_id, workflow_name)`` and ranks them by descending
    ``created_at``.  Only rank-1 rows (i.e. the newest execution per
    pipeline) are returned.

    Parameters
    ----------
    dataset_id:
        The dataset whose pipeline history is queried.

    Returns
    -------
    list[WorkflowRun]
        One :class:`WorkflowRun` per distinct ``workflow_name``,
        representing the most recent execution.
    """
    relational_adapter = get_db_adapter()

    async with relational_adapter.get_async_session() as db_session:
        recency_rank = (
            func.row_number()
            .over(
                partition_by=[
                    WorkflowRun.dataset_id,
                    WorkflowRun.workflow_name,
                ],
                order_by=WorkflowRun.created_at.desc(),
            )
            .label("_recency_rank")
        )

        windowed_subquery = select(WorkflowRun, recency_rank).where(WorkflowRun.dataset_id == dataset_id).subquery()

        run_alias = aliased(WorkflowRun, windowed_subquery)

        top_runs_stmt = select(run_alias).where(windowed_subquery.c._recency_rank == 1)

        cursor = await db_session.execute(top_runs_stmt)
        latest_runs = list(cursor.scalars().all())

    _logger.debug(
        "mflow.pipeline.runs_by_dataset dataset_id=%s count=%d",
        dataset_id,
        len(latest_runs),
    )
    return latest_runs
