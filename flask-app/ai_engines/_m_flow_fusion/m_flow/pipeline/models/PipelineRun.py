"""
SQLAlchemy model for workflow execution records.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(enum.Enum):
    """Lifecycle states for a workflow run."""

    DATASET_PROCESSING_INITIATED = "DATASET_PROCESSING_INITIATED"
    DATASET_PROCESSING_STARTED = "DATASET_PROCESSING_STARTED"
    DATASET_PROCESSING_COMPLETED = "DATASET_PROCESSING_COMPLETED"
    DATASET_PROCESSING_ERRORED = "DATASET_PROCESSING_ERRORED"


RunStatus.INITIATED = RunStatus.DATASET_PROCESSING_INITIATED
RunStatus.STARTED = RunStatus.DATASET_PROCESSING_STARTED
RunStatus.COMPLETED = RunStatus.DATASET_PROCESSING_COMPLETED
RunStatus.ERRORED = RunStatus.DATASET_PROCESSING_ERRORED


class WorkflowRun(Base):
    """
    Tracks individual workflow executions.
    """

    __tablename__ = "workflow_runs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime(timezone=True), default=_utc_now)

    status = Column(Enum(RunStatus))
    workflow_run_id = Column(PG_UUID(as_uuid=True), index=True)
    workflow_name = Column(String(255))
    workflow_id = Column(PG_UUID(as_uuid=True), index=True)
    dataset_id = Column(PG_UUID(as_uuid=True), index=True)
    run_detail = Column(JSON)
