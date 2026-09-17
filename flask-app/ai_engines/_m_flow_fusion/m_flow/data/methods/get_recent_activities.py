"""
Recent Activities Aggregation
=============================

Aggregates activity data from multiple tables (queries, pipeline_runs)
into a unified activity feed for the dashboard.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, union_all, desc, literal, cast, String

from m_flow.adapters.relational import get_db_adapter
from m_flow.shared.utils import to_iso_z


async def get_recent_activities(
    user_id: Optional[UUID] = None,
    limit: int = 20,
) -> List[dict]:
    """
    Get recent activities by aggregating from multiple tables.

    Aggregates data from:
    - queries: search activities
    - pipeline_runs: ingest activities

    Args:
        user_id: Filter activities by user (optional for single-user mode)
        limit: Maximum number of activities to return

    Returns:
        List of activity dictionaries with unified structure
    """
    # Lazy imports to avoid circular dependencies
    from m_flow.search.models.Query import Query
    from m_flow.pipeline.models.PipelineRun import WorkflowRun

    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Search activities from queries table
        search_query = select(
            literal("search").label("type"),
            Query.id.label("id"),
            Query.text.label("title"),
            Query.query_type.label("description"),
            Query.created_at.label("created_at"),
        )
        if user_id:
            search_query = search_query.where(Query.user_id == user_id)

        # Ingest activities from pipeline_runs table
        # Note: status is stored as full enum value (e.g., DATASET_PROCESSING_COMPLETED)
        from m_flow.pipeline.models.PipelineRun import RunStatus

        ingest_query = select(
            literal("ingest").label("type"),
            WorkflowRun.id.label("id"),
            WorkflowRun.workflow_name.label("title"),
            cast(WorkflowRun.status, String).label("description"),
            WorkflowRun.created_at.label("created_at"),
        ).where(
            WorkflowRun.status.in_(
                [
                    RunStatus.STARTED,
                    RunStatus.COMPLETED,
                ]
            )
        )

        # Use subquery() to avoid SQLAlchemy deprecation warning
        combined = union_all(search_query, ingest_query).subquery()

        # Select from subquery with ordering and limit
        final_query = select(combined).order_by(desc(combined.c.created_at)).limit(limit)

        result = await session.execute(final_query)
        rows = result.all()

        return [
            {
                "id": str(row.id),
                "type": row.type,
                "title": _format_title(row.type, row.title),
                "description": _format_description(row.type, row.description),
                "status": _map_status(row.type, row.description),
                # Ensure UTC timezone is included for correct frontend parsing.
                # Uses ``to_iso_z`` so timezone-aware values from Postgres
                # (``timestamp with time zone``) do not produce ``+00:00Z``
                # double markers that pydantic rejects (issue #116).
                "created_at": to_iso_z(row.created_at),
            }
            for row in rows
        ]


def _format_title(activity_type: str, raw_title: Optional[str]) -> str:
    """Format activity title for display."""
    if not raw_title:
        return "Unknown activity"

    if activity_type == "search":
        truncated = raw_title[:50] + "..." if len(raw_title) > 50 else raw_title
        return f'Search: "{truncated}"'
    elif activity_type == "ingest":
        name_map = {
            "add_pipeline": "Document added",
            "memorize_pipeline": "Knowledge graph updated",
        }
        return name_map.get(raw_title, raw_title)
    return raw_title


def _format_description(activity_type: str, raw_desc: Optional[str]) -> Optional[str]:
    """Format activity description."""
    if not raw_desc:
        return None

    if activity_type == "search":
        return f"Mode: {raw_desc}"
    elif activity_type == "ingest":
        # Handle both short and full enum names
        status_map = {
            "STARTED": "Processing...",
            "COMPLETED": "Completed successfully",
            "DATASET_PROCESSING_STARTED": "Processing...",
            "DATASET_PROCESSING_COMPLETED": "Completed successfully",
            "RunStatus.STARTED": "Processing...",
            "RunStatus.COMPLETED": "Completed successfully",
            "RunStatus.DATASET_PROCESSING_STARTED": "Processing...",
            "RunStatus.DATASET_PROCESSING_COMPLETED": "Completed successfully",
        }
        return status_map.get(raw_desc, raw_desc)
    return raw_desc


def _map_status(activity_type: str, raw_status: Optional[str]) -> str:
    """Map to unified status."""
    if activity_type == "ingest" and raw_status:
        # Handle both short and full enum names
        if "COMPLETED" in raw_status:
            return "success"
        elif "STARTED" in raw_status:
            return "pending"
        elif "ERRORED" in raw_status:
            return "error"
    return "success"
