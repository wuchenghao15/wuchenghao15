"""
Query single pipeline run by dataset and pipeline name.

Returns the most recent run for a specific dataset/pipeline pair.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from m_flow.adapters.relational import get_db_adapter
from ..models import WorkflowRun


async def get_pipeline_run_by_dataset(
    dataset_id: UUID,
    workflow_name: str,
) -> Optional[WorkflowRun]:
    """
    Fetch the latest pipeline run for a dataset.

    Args:
        dataset_id: Target dataset identifier.
        workflow_name: Name of pipeline to query.

    Returns:
        Most recent WorkflowRun or None if not found.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Rank runs by creation time within dataset
        ranked_subq = (
            select(
                WorkflowRun,
                func.row_number()
                .over(
                    partition_by=WorkflowRun.dataset_id,
                    order_by=WorkflowRun.created_at.desc(),
                )
                .label("rank"),
            )
            .where(WorkflowRun.dataset_id == dataset_id)
            .where(WorkflowRun.workflow_name == workflow_name)
            .subquery()
        )

        alias = aliased(WorkflowRun, ranked_subq)
        query = select(alias).where(ranked_subq.c.rank == 1)

        result = await session.execute(query)
        return result.scalars().first()
