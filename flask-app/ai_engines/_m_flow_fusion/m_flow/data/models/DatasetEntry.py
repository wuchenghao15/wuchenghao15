"""
Association table linking datasets to data records.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DatasetEntry(Base):
    """
    Many-to-many join table for Dataset ↔ Data relationship.
    """

    __tablename__ = "dataset_data"

    dataset_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    data_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("data.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(DateTime(timezone=True), default=_utc_now)
