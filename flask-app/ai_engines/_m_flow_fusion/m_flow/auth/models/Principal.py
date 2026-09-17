"""
Base principal model for polymorphic identity.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Principal(Base):
    """
    Base class for security principals (users, groups, service accounts).
    """

    __tablename__ = "principals"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    type = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), onupdate=_utc_now)

    __mapper_args__ = {
        "polymorphic_identity": "principal",
        "polymorphic_on": "type",
    }
