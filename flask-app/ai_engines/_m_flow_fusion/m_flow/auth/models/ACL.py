"""
Access Control List model for dataset permissions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from m_flow.adapters.relational import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ACL(Base):
    """
    Links principals to permissions for specific datasets.
    """

    __tablename__ = "acls"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    principal_id = Column(PG_UUID(as_uuid=True), ForeignKey("principals.id"))
    permission_id = Column(PG_UUID(as_uuid=True), ForeignKey("permissions.id"))
    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), onupdate=_utc_now)

    principal = relationship("Principal")
    permission = relationship("Permission")
    dataset = relationship("Dataset", back_populates="acls")
