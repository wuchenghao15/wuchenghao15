"""
Dismiss (mark as errored) a stale pipeline run.

Used to clean up pipelines that appear stuck or orphaned.

Note: With deterministic pipeline_run_ids (same id for multiple runs),
queries use ORDER BY created_at DESC LIMIT 1 to ensure we always
dismiss the latest active record for a given run_id.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4

from sqlalchemy import or_, select

from m_flow.adapters.relational import get_db_adapter
from m_flow.pipeline.models import WorkflowRun, RunStatus
from m_flow.shared.logging_utils import get_logger

logger = get_logger("pipeline_dismiss")


async def dismiss_pipeline_run(workflow_run_id: UUID) -> Dict[str, Any]:
    """
    Dismiss a pipeline by adding an ERRORED record.

    This marks the pipeline as no longer active so it won't appear
    in the active pipelines list.

    Note: Supports dismissing pipelines in both STARTED and INITIATED states.
    Uses ORDER BY created_at DESC LIMIT 1 to handle deterministic run_ids
    where multiple records may exist for the same run_id.

    Args:
        workflow_run_id: The pipeline run to dismiss.

    Returns:
        Dict with success status and message.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Find the latest STARTED or INITIATED record for this run_id
        # ORDER BY created_at DESC LIMIT 1 ensures we get the most recent one
        stmt = (
            select(WorkflowRun)
            .where(
                WorkflowRun.workflow_run_id == workflow_run_id,
                or_(
                    WorkflowRun.status == RunStatus.STARTED,
                    WorkflowRun.status == RunStatus.INITIATED,
                    WorkflowRun.status == RunStatus.DATASET_PROCESSING_STARTED,
                    WorkflowRun.status == RunStatus.DATASET_PROCESSING_INITIATED,
                ),
            )
            .order_by(WorkflowRun.created_at.desc())
            .limit(1)
        )
        record = await session.scalar(stmt)

        if not record:
            return {
                "success": False,
                "message": f"No active pipeline found with ID {workflow_run_id}",
            }

        # Create an ERRORED record to mark it as dismissed
        dismissed_record = WorkflowRun(
            id=uuid4(),
            workflow_run_id=workflow_run_id,
            workflow_id=record.workflow_id,
            workflow_name=record.workflow_name,
            dataset_id=record.dataset_id,
            status=RunStatus.ERRORED,
            run_detail={
                "dismissed": True,
                "dismissed_at": datetime.now(timezone.utc).isoformat(),
                "reason": "Manually dismissed by user",
            },
            created_at=datetime.now(timezone.utc),
        )

        session.add(dismissed_record)
        await session.commit()

        logger.info(f"Dismissed pipeline {workflow_run_id}")

        return {
            "success": True,
            "message": f"Pipeline {workflow_run_id} dismissed successfully",
        }
