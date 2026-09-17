"""
Association table linking users to tenants.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserTenant(Base):
    """
    Many-to-many join table for User ↔ Tenant relationship.
    """

    __tablename__ = "user_tenants"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)
