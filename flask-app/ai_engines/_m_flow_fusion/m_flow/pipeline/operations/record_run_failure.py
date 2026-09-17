"""
Pipeline error logging.

Persists pipeline run errors to the database.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.models import Data
from m_flow.pipeline.models import WorkflowRun, RunStatus


async def record_run_failure(
    workflow_run_id: UUID,
    workflow_id: str,
    workflow_name: str,
    dataset_id: UUID,
    data: Any,
    e: Exception,
) -> WorkflowRun:
    """
    Log pipeline error to database.

    Args:
        workflow_run_id: Run identifier.
        workflow_id: Pipeline identifier.
        workflow_name: Pipeline name.
        dataset_id: Target dataset.
        data: Data being processed.
        e: Exception that occurred.

    Returns:
        Created WorkflowRun record.
    """
    # Serialize data info
    if not data:
        data_repr = "None"
    elif isinstance(data, list) and all(isinstance(x, Data) for x in data):
        data_repr = [str(x.id) for x in data]
    else:
        data_repr = str(data)

    run = WorkflowRun(
        workflow_run_id=workflow_run_id,
        workflow_name=workflow_name,
        workflow_id=workflow_id,
        status=RunStatus.DATASET_PROCESSING_ERRORED,
        dataset_id=dataset_id,
        run_detail={"data": data_repr, "error": str(e)},
    )

    engine = get_db_adapter()
    async with engine.get_async_session() as session:
        session.add(run)
        await session.commit()

    return run
