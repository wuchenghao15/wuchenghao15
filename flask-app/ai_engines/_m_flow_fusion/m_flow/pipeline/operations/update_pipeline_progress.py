"""
Pipeline progress update operations.

Updates progress info in the STARTED record's run_detail JSON field.
No database migration required - uses existing JSON column.

Note: With deterministic pipeline_run_ids (same id for multiple runs),
queries use ORDER BY created_at DESC LIMIT 1 to ensure we always
update the latest STARTED record for a given run_id.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, cast, String

from m_flow.adapters.relational import get_db_adapter
from m_flow.pipeline.models import WorkflowRun, RunStatus
from m_flow.shared.logging_utils import get_logger

logger = get_logger("pipeline_progress")


async def update_pipeline_progress(
    workflow_run_id: UUID,
    total_items: Optional[int] = None,
    processed_items: Optional[int] = None,
    current_step: Optional[str] = None,
) -> None:
    """
    Update progress in the STARTED record's run_detail JSON.

    This is fire-and-forget - failures are logged but don't block pipeline.

    Note: Uses ORDER BY created_at DESC LIMIT 1 to handle deterministic
    run_ids where multiple STARTED records may exist for the same run_id.
    """
    try:
        engine = get_db_adapter()

        # Convert to hex string without dashes for SQLite compatibility
        # Handle both UUID objects and string inputs
        if isinstance(workflow_run_id, str):
            run_id_hex = workflow_run_id.replace("-", "")
        else:
            run_id_hex = workflow_run_id.hex

        async with engine.get_async_session() as session:
            # Use cast to avoid SQLAlchemy trying to bind UUID type
            # ORDER BY created_at DESC LIMIT 1 ensures we get the latest STARTED record
            stmt = (
                select(WorkflowRun)
                .where(
                    cast(WorkflowRun.workflow_run_id, String) == run_id_hex,
                    WorkflowRun.status == RunStatus.STARTED,
                )
                .order_by(WorkflowRun.created_at.desc())
                .limit(1)
            )
            logger.debug(f"[progress] Query: run_id_hex={run_id_hex}")
            record = await session.scalar(stmt)

            if not record:
                logger.warning(f"[progress] No STARTED record found for {workflow_run_id} (hex={run_id_hex})")
                return

            logger.debug(f"[progress] Found record: {record.workflow_run_id}")

            run_detail = dict(record.run_detail) if record.run_detail else {}
            progress = run_detail.get("progress", {})

            if total_items is not None:
                progress["total_items"] = total_items
            if processed_items is not None:
                progress["processed_items"] = processed_items
            if current_step is not None:
                progress["current_step"] = current_step

            progress["updated_at"] = datetime.now(timezone.utc).isoformat()
            run_detail["progress"] = progress

            record.run_detail = run_detail

            # Force SQLAlchemy to detect the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(record, "run_detail")

            await session.commit()
            logger.info(
                f"[progress] Updated run_id={workflow_run_id}: step={current_step}, processed={processed_items}"
            )

    except Exception as e:
        logger.warning(f"[progress] Failed to update for {workflow_run_id}: {e}")


async def set_pipeline_started(
    workflow_run_id: UUID,
    total_items: int,
) -> None:
    """
    Initialize progress tracking when pipeline starts.

    Note: Uses ORDER BY created_at DESC LIMIT 1 to handle deterministic
    run_ids where multiple STARTED records may exist for the same run_id.
    """
    try:
        engine = get_db_adapter()

        # Convert to hex string without dashes for SQLite compatibility
        # Handle both UUID objects and string inputs
        if isinstance(workflow_run_id, str):
            run_id_hex = workflow_run_id.replace("-", "")
        else:
            run_id_hex = workflow_run_id.hex

        async with engine.get_async_session() as session:
            # Use cast to avoid SQLAlchemy trying to bind UUID type
            # ORDER BY created_at DESC LIMIT 1 ensures we get the latest STARTED record
            stmt = (
                select(WorkflowRun)
                .where(
                    cast(WorkflowRun.workflow_run_id, String) == run_id_hex,
                    WorkflowRun.status == RunStatus.STARTED,
                )
                .order_by(WorkflowRun.created_at.desc())
                .limit(1)
            )
            record = await session.scalar(stmt)

            if not record:
                logger.debug(f"No STARTED record found for {workflow_run_id}")
                return

            run_detail = dict(record.run_detail) if record.run_detail else {}
            run_detail["progress"] = {
                "total_items": total_items,
                "processed_items": 0,
                "current_step": "Initializing",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            record.run_detail = run_detail

            # Force SQLAlchemy to detect the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(record, "run_detail")

            await session.commit()

    except Exception as e:
        logger.warning(f"Failed to set pipeline started for {workflow_run_id}: {e}")
