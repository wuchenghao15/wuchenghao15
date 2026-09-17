"""
Dataset Model
=============

SQLAlchemy model representing a collection of related data items.
Datasets are the primary organizational unit for user content.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from m_flow.adapters.relational import Base
from m_flow.shared.utils import to_iso_z

from .DatasetEntry import DatasetEntry

if TYPE_CHECKING:
    pass


def _current_utc_timestamp() -> datetime:
    """Generate current UTC timestamp."""
    return datetime.now(timezone.utc)


class Dataset(Base):
    """
    Collection of related data records.

    Datasets serve as containers for grouping related content
    such as documents, files, or other data items. Each dataset
    is owned by a user and optionally belongs to a tenant.

    Attributes
    ----------
    id : UUID
        Primary key.
    name : str
        Human-readable dataset name.
    owner_id : UUID
        User who owns this dataset.
    tenant_id : UUID | None
        Optional tenant association.
    created_at : datetime
        Creation timestamp.
    updated_at : datetime | None
        Last modification timestamp.
    acls : list[ACL]
        Access control entries for this dataset.
    data : list[Data]
        Data items in this dataset.
    """

    __tablename__ = "datasets"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Attributes
    name = Column(Text)
    owner_id = Column(PG_UUID(as_uuid=True), index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), index=True, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=_current_utc_timestamp)
    updated_at = Column(DateTime(timezone=True), onupdate=_current_utc_timestamp)

    # Relationships
    acls = relationship(
        "ACL",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    data = relationship(
        "Data",
        secondary=DatasetEntry.__tablename__,
        back_populates="datasets",
        lazy="noload",
        cascade="all, delete",
    )

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize dataset to JSON-compatible dictionary.

        Returns
        -------
        dict
            Dictionary with all dataset fields.
        """
        return {
            "id": str(self.id),
            "name": self.name,
            # Use ``to_iso_z`` to emit a single ``Z`` suffix that is well-formed
            # whether the column stored a naive or timezone-aware datetime
            # (issue #116: ``+ "Z"`` produced ``+00:00Z`` on Postgres).
            "createdAt": to_iso_z(self.created_at),
            "updatedAt": to_iso_z(self.updated_at),
            "ownerId": str(self.owner_id),
            "tenantId": str(self.tenant_id) if self.tenant_id else None,
            "data": [item.to_json() for item in self.data],
        }
