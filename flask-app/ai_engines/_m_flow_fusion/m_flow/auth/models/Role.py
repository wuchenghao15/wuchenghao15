"""Role model definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship

from .Principal import Principal
from .UserRole import UserRole

if TYPE_CHECKING:
    pass


class Role(Principal):
    """
    Role entity for role-based access control.

    Organizes permissions into named roles within tenant scope.
    """

    __tablename__ = "roles"

    id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("principals.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name = Column(String(128), nullable=False, index=True)
    tenant_id = Column(PgUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    users = relationship(
        "User",
        secondary=UserRole.__tablename__,
        back_populates="roles",
    )
    tenant = relationship(
        "Tenant",
        back_populates="roles",
        foreign_keys=[tenant_id],
    )

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_id_name"),)
    __mapper_args__ = {"polymorphic_identity": "role"}
