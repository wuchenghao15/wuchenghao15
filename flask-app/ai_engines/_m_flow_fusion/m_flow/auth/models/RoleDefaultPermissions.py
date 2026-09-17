"""
M-Flow role ↔ permission association model.

Maps each authorisation role to the set of permissions it receives by
default at creation time.  Implemented as a composite-key join table
with an audit timestamp.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from m_flow.adapters.relational import Base


def _current_utc_timestamp() -> datetime:
    """Return the current moment in UTC (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


class RoleDefaultPermissions(Base):
    """Join table linking roles to their initial permission grants."""

    __tablename__ = "role_default_permissions"

    role_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=_current_utc_timestamp,
    )
