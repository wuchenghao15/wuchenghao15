"""
Pipeline Run Retrieval
======================

Utility for fetching pipeline run records from the database.

Note: With deterministic pipeline_run_ids (same id for multiple runs),
this function returns the latest record for a given run_id using
ORDER BY created_at DESC LIMIT 1.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.pipeline.models import WorkflowRun


async def get_pipeline_run(workflow_run_id: UUID) -> Optional[WorkflowRun]:
    """
    Fetch the latest pipeline run record by its identifier.

    With deterministic run_ids, multiple records may exist for the same
    run_id (e.g., INITIATED, STARTED, COMPLETED from different runs).
    This function returns the most recent one.

    Parameters
    ----------
    workflow_run_id : UUID
        Unique identifier of the pipeline run.

    Returns
    -------
    WorkflowRun | None
        The latest pipeline run if found, None otherwise.
    """
    db = get_db_adapter()

    async with db.get_async_session() as session:
        stmt = (
            select(WorkflowRun)
            .filter(WorkflowRun.workflow_run_id == workflow_run_id)
            .order_by(WorkflowRun.created_at.desc())
            .limit(1)
        )
        return await session.scalar(stmt)
