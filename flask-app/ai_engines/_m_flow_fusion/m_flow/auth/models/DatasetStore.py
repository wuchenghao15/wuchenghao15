"""
Model for dataset-specific database configuration.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DatasetStore(Base):
    """
    Stores per-dataset database connection configuration.
    """

    __tablename__ = "dataset_database"

    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="CASCADE"), index=True)
    dataset_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    vector_database_name = Column(String(256), nullable=False)
    graph_database_name = Column(String(256), nullable=False)
    vector_database_provider = Column(String(64), nullable=False)
    graph_database_provider = Column(String(64), nullable=False)
    graph_dataset_database_handler = Column(String(64), nullable=False)
    vector_dataset_database_handler = Column(String(64), nullable=False)
    vector_database_url = Column(String(512), nullable=True)
    graph_database_url = Column(String(512), nullable=True)
    vector_database_key = Column(String(256), nullable=True)
    graph_database_key = Column(String(256), nullable=True)
    graph_database_connection_info = Column(JSON, nullable=False, server_default=text("'{}'"))
    vector_database_connection_info = Column(JSON, nullable=False, server_default=text("'{}'"))

    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), onupdate=_utc_now)
