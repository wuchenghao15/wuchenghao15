"""
User persistence model and companion Pydantic schemas.

Defines the SQLAlchemy ORM mapping for application users and the
FastAPI-Users-compatible read / create / update schemas used by the
authentication endpoints.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID as PyUUID

from fastapi_users import schemas
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .Principal import Principal
from .UserRole import UserRole
from .UserTenant import UserTenant


class User(SQLAlchemyBaseUserTableUUID, Principal):
    """
    Registered application user.

    Inherits identity columns from :class:`Principal` and authentication
    fields from ``SQLAlchemyBaseUserTableUUID``.  The primary key is a
    foreign key into the ``principals`` table so that the single-table
    polymorphic hierarchy is preserved.
    """

    __tablename__ = "users"

    id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("principals.id", ondelete="CASCADE"),
        primary_key=True,
    )

    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"))

    roles = relationship(
        "Role",
        secondary=UserRole.__tablename__,
        back_populates="users",
    )

    tenants = relationship(
        "Tenant",
        secondary=UserTenant.__tablename__,
        back_populates="users",
    )

    acls = relationship(
        "ACL",
        back_populates="principal",
        cascade="all, delete",
    )

    __mapper_args__ = {"polymorphic_identity": "user"}


# ------------------------------------------------------------------
# Pydantic schemas consumed by FastAPI-Users routers
# ------------------------------------------------------------------


class UserRead(schemas.BaseUser[PyUUID]):
    """Outbound representation of a user record."""

    tenant_id: Optional[PyUUID] = None


class UserCreate(schemas.BaseUserCreate):
    """Inbound payload for user registration (email-verified by default)."""

    is_verified: bool = True


class UserUpdate(schemas.BaseUserUpdate):
    """Inbound payload for partial user profile updates."""

    pass
