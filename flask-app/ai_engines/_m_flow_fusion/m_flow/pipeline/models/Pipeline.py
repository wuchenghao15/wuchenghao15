"""
SQLAlchemy model for pipeline definitions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, relationship

from m_flow.adapters.relational import Base

if TYPE_CHECKING:
    from .Task import Stage

from .PipelineTask import PipelineTask


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Pipeline(Base):
    """
    Represents a reusable pipeline configuration.
    """

    __tablename__ = "pipelines"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255))
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), onupdate=_utc_now)

    tasks: Mapped[List["Task"]] = relationship(
        secondary=PipelineTask.__tablename__,
        back_populates="pipeline",
    )
