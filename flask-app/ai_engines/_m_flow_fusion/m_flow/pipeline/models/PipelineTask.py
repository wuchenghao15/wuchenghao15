"""
Association table linking pipelines to tasks.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineTask(Base):
    """
    Many-to-many join table for Pipeline ↔ Task relationship.
    """

    __tablename__ = "pipeline_task"

    workflow_id = Column(
        "pipeline",
        PG_UUID(as_uuid=True),
        ForeignKey("pipelines.id"),
        primary_key=True,
    )
    task_id = Column(
        "task",
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id"),
        primary_key=True,
    )
    created_at = Column(DateTime(timezone=True), default=_utc_now)
