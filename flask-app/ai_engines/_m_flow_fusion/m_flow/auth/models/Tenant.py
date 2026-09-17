"""
Tenant Model
============

Multi-tenancy support model for organizational isolation.
Tenants group users and data into separate organizational units.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .Principal import Principal
from .UserTenant import UserTenant

if TYPE_CHECKING:
    pass


class Tenant(Principal):
    """
    Organizational unit for multi-tenant data isolation.

    Tenants provide logical separation of data and users within
    the M-flow system. Each tenant has its own set of users,
    roles, and datasets.

    Attributes
    ----------
    id : UUID
        Primary key inherited from Principal.
    name : str
        Unique tenant name/identifier.
    owner_id : UUID
        ID of the user who owns this tenant.
    users : list[User]
        Users belonging to this tenant.
    roles : list[Role]
        Roles defined within this tenant.
    """

    __tablename__ = "tenants"

    # Primary key linking to principals table
    id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("principals.id"),
        primary_key=True,
    )

    # Tenant attributes
    name = Column(String(256), unique=True, nullable=False, index=True)
    owner_id = Column(PG_UUID(as_uuid=True), index=True)

    # Relationships
    users = relationship(
        "User",
        secondary=UserTenant.__tablename__,
        back_populates="tenants",
    )

    roles = relationship(
        "Role",
        back_populates="tenant",
        foreign_keys="[Role.tenant_id]",
    )

    # Polymorphic identity for Principal hierarchy
    __mapper_args__ = {"polymorphic_identity": "tenant"}
