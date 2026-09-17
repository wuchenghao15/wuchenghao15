"""Query model for search operations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Query(Base):
    """Stores user search queries."""

    __tablename__ = "queries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    text = Column(String(2048))
    query_type = Column(String(64))
    user_id = Column(PG_UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), onupdate=_utc_now)
