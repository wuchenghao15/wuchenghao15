"""
Pipeline run initiation logging.
"""

from __future__ import annotations

from uuid import UUID

from m_flow.adapters.relational import get_db_adapter
from m_flow.pipeline.models import WorkflowRun, RunStatus
from m_flow.pipeline.utils import generate_workflow_run_id


async def record_run_initiated(
    workflow_id: UUID,
    workflow_name: str,
    dataset_id: UUID,
) -> WorkflowRun:
    """Create initial pipeline run record with INITIATED status."""
    run_id = generate_workflow_run_id(workflow_id, dataset_id)

    record = WorkflowRun(
        workflow_run_id=run_id,
        workflow_name=workflow_name,
        workflow_id=workflow_id,
        status=RunStatus.DATASET_PROCESSING_INITIATED,
        dataset_id=dataset_id,
        run_detail={},
    )

    db = get_db_adapter()
    async with db.get_async_session() as s:
        s.add(record)
        await s.commit()

    return record
