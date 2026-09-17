"""SQLAlchemy model for persistent face ↔ dataset mappings."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PlaygroundFaceMapping(Base):
    """Persistent mapping between fanjing-face-recognition registered_id and M-Flow dataset.

    Multiple rows per (owner, face) pair allowed — one face can link to many datasets.
    Unique constraint is on (owner, face, dataset) to prevent duplicate links.
    """

    __tablename__ = "playground_face_mappings"
    __table_args__ = (UniqueConstraint("owner_id", "face_registered_id", "dataset_id", name="uq_owner_face_dataset"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    face_registered_id = Column(Integer, nullable=False)
    dataset_id = Column(PG_UUID(as_uuid=True), nullable=False)
    display_name = Column(Text, nullable=False, default="")
    auto_created = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
