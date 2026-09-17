"""
SQLAlchemy model for task definitions.
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
    from .Pipeline import Pipeline

from .PipelineTask import PipelineTask


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Stage(Base):
    """
    Represents a reusable task that can be part of multiple pipelines.
    """

    __tablename__ = "tasks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255))
    description = Column(Text, nullable=True)
    executable = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), onupdate=_utc_now)

    pipelines: Mapped[List["Pipeline"]] = relationship(
        secondary=PipelineTask.__tablename__,
        back_populates="tasks",
    )

    # Alias (original typo)
    @property
    def datasets(self) -> List["Pipeline"]:
        return self.pipelines
