"""
Query pipeline status for multiple datasets.

Returns a mapping of dataset IDs to their latest pipeline run status.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from m_flow.adapters.relational import get_db_adapter
from ..models import WorkflowRun


async def get_workflow_status(
    dataset_ids: list[UUID],
    workflow_name: str,
) -> dict[str, str]:
    """
    Get latest pipeline status for each dataset.

    Args:
        dataset_ids: List of datasets to query.
        workflow_name: Name of the pipeline to check.

    Returns:
        Dict mapping dataset_id (str) to status string.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Subquery with row numbers ranked by recency
        ranked = (
            select(
                WorkflowRun,
                func.row_number()
                .over(
                    partition_by=WorkflowRun.dataset_id,
                    order_by=WorkflowRun.created_at.desc(),
                )
                .label("rank"),
            )
            .where(WorkflowRun.dataset_id.in_(dataset_ids))
            .where(WorkflowRun.workflow_name == workflow_name)
            .subquery()
        )

        alias = aliased(WorkflowRun, ranked)
        query = select(alias).where(ranked.c.rank == 1)

        rows = await session.execute(query)
        runs = rows.scalars().all()

        return {str(run.dataset_id): run.status for run in runs}
