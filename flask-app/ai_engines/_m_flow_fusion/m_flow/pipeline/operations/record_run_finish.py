"""
Pipeline completion logging.

Records successful pipeline run to database.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.models import Data
from m_flow.pipeline.models import WorkflowRun, RunStatus


async def record_run_finish(
    workflow_run_id: UUID,
    workflow_id: str,
    workflow_name: str,
    dataset_id: UUID,
    data: Any,
) -> WorkflowRun:
    """
    Record pipeline completion.

    Args:
        workflow_run_id: Run identifier.
        workflow_id: Pipeline identifier.
        workflow_name: Human-readable name.
        dataset_id: Processed dataset.
        data: Input data summary.

    Returns:
        Persisted WorkflowRun record.
    """
    # Format data for logging
    data_summary = _summarize_data(data)

    record = WorkflowRun(
        workflow_run_id=workflow_run_id,
        workflow_name=workflow_name,
        workflow_id=workflow_id,
        status=RunStatus.DATASET_PROCESSING_COMPLETED,
        dataset_id=dataset_id,
        run_detail={"data": data_summary},
    )

    engine = get_db_adapter()
    async with engine.get_async_session() as sess:
        sess.add(record)
        await sess.commit()

    return record


def _summarize_data(data: Any) -> Any:
    """Convert data to loggable format."""
    if not data:
        return "None"

    if isinstance(data, list) and all(isinstance(d, Data) for d in data):
        return [str(d.id) for d in data]

    return str(data)
