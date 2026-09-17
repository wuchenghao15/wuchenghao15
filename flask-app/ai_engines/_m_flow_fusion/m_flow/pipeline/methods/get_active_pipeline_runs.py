"""
Query active (running) pipeline runs.

Returns pipelines that are currently in progress based on their latest status.
Uses ROW_NUMBER window function to get the most recent status for each
(dataset_id, workflow_name) combination.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import func, select

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.models import Dataset
from m_flow.pipeline.models import WorkflowRun, RunStatus
from m_flow.shared.utils import to_iso_z


async def get_active_pipeline_runs() -> List[Dict[str, Any]]:
    """
    Get all currently active pipeline runs based on latest status.

    The pipeline_runs table is append-only (multiple records per workflow_run_id).
    This function uses a ROW_NUMBER window function to find the latest status
    for each (dataset_id, workflow_name) combination, then filters for active
    statuses (INITIATED or STARTED).

    This approach correctly handles:
    1. Deterministic run_ids (same id for INITIATED/STARTED/COMPLETED)
    2. Multiple runs of the same pipeline on the same dataset
    3. Dismissed pipelines that are re-processed

    Returns:
        List of active pipeline info dicts with progress data.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        session.expire_all()

        # Step 1: Create subquery with ROW_NUMBER to rank records by recency
        # For each (dataset_id, workflow_name), rank records by created_at DESC
        ranked_subq = select(
            WorkflowRun.id,
            WorkflowRun.workflow_run_id,
            WorkflowRun.dataset_id,
            WorkflowRun.workflow_name,
            WorkflowRun.workflow_id,
            WorkflowRun.status,
            WorkflowRun.run_detail,
            WorkflowRun.created_at,
            func.row_number()
            .over(
                partition_by=[WorkflowRun.dataset_id, WorkflowRun.workflow_name],
                order_by=WorkflowRun.created_at.desc(),
            )
            .label("rank"),
        ).subquery()

        # Step 2: Select only rank=1 (latest) records with active status
        # Join with Dataset to get dataset_name
        stmt = (
            select(
                ranked_subq.c.workflow_run_id,
                ranked_subq.c.dataset_id,
                ranked_subq.c.workflow_name,
                ranked_subq.c.workflow_id,
                ranked_subq.c.status,
                ranked_subq.c.run_detail,
                ranked_subq.c.created_at,
                Dataset.name.label("dataset_name"),
            )
            .outerjoin(Dataset, ranked_subq.c.dataset_id == Dataset.id)
            .where(ranked_subq.c.rank == 1)
            .where(
                ranked_subq.c.status.in_(
                    [
                        RunStatus.STARTED,
                        RunStatus.DATASET_PROCESSING_STARTED,
                    ]
                )
            )
            .order_by(ranked_subq.c.created_at.desc())
        )

        result = await session.execute(stmt)
        rows = result.all()

    # Step 3: Format results
    active_pipelines = []
    for row in rows:
        run_detail = row.run_detail or {}
        progress = run_detail.get("progress", {})

        # Handle status - it may be an enum or a string value
        status_value = row.status
        if hasattr(status_value, "value"):
            status_value = status_value.value

        active_pipelines.append(
            {
                "workflow_run_id": str(row.workflow_run_id),
                "dataset_id": str(row.dataset_id) if row.dataset_id else None,
                "dataset_name": row.dataset_name,
                "workflow_name": row.workflow_name or "Pipeline",
                "status": status_value if status_value else "unknown",
                "total_items": progress.get("total_items"),
                "processed_items": progress.get("processed_items", 0),
                "current_step": progress.get("current_step"),
                "started_at": progress.get("started_at"),
                "updated_at": progress.get("updated_at"),
                "created_at": to_iso_z(row.created_at),
            }
        )

    return active_pipelines
