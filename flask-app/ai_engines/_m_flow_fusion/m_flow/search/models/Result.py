"""Result model for search operations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Result(Base):
    """Stores search result payloads."""

    __tablename__ = "results"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    value = Column(Text)
    query_id = Column(PG_UUID(as_uuid=True))
    user_id = Column(PG_UUID(as_uuid=True), index=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), onupdate=_utc_now)
