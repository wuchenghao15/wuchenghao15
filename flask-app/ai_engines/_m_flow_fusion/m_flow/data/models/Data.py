"""
Data Model
==========

SQLAlchemy model representing ingested data records.
Each Data record represents a single file or content item
that has been processed through the ingestion pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from m_flow.adapters.relational import Base
from m_flow.shared.utils import to_iso_z

from .DatasetEntry import DatasetEntry

if TYPE_CHECKING:
    pass


def _current_utc_timestamp() -> datetime:
    """Generate current UTC timestamp."""
    return datetime.now(timezone.utc)


class Data(Base):
    """
    Represents an ingested content item.

    Stores metadata about ingested files including location,
    format information, and processing status.

    Attributes
    ----------
    id : UUID
        Primary key.
    name : str
        Original file name.
    extension : str
        File extension after processing.
    mime_type : str
        MIME type after processing.
    original_extension : str | None
        Original file extension.
    original_mime_type : str | None
        Original MIME type.
    parser_name : str
        Parser used to load the data.
    processed_path : str
        Path to processed data.
    source_path : str
        Path to original data.
    owner_id : UUID
        User who owns this data.
    tenant_id : UUID | None
        Optional tenant association.
    content_hash : str
        Hash of processed content.
    source_digest : str
        Hash of raw content.
    external_metadata : dict
        User-provided metadata.
    graph_scope : dict | None
        Associated graph nodes.
    workflow_state : dict
        Processing workflow status.
    token_count : int
        Token count for text content.
    data_size : int | None
        Size in bytes.
    created_at : datetime
        Creation timestamp.
    updated_at : datetime | None
        Last update timestamp.
    datasets : list[Dataset]
        Datasets containing this data.
    """

    __tablename__ = "data"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # File metadata
    name = Column(String(512))
    extension = Column(String(32))
    mime_type = Column(String(128))
    original_extension = Column(String(32), nullable=True)
    original_mime_type = Column(String(128), nullable=True)
    parser_name = Column(String(64))

    # Storage locations
    processed_path = Column(String(1024))
    source_path = Column(String(1024))

    # Ownership
    owner_id = Column(PG_UUID(as_uuid=True), index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), index=True, nullable=True)

    # Content tracking
    content_hash = Column(String(128))
    source_digest = Column(String(128))
    external_metadata = Column(JSON)
    graph_scope = Column(JSON, nullable=True)
    workflow_state = Column(MutableDict.as_mutable(JSON))
    token_count = Column(Integer)
    data_size = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=_current_utc_timestamp)
    updated_at = Column(DateTime(timezone=True), onupdate=_current_utc_timestamp)

    # Relationships
    datasets = relationship(
        "Dataset",
        secondary=DatasetEntry.__tablename__,
        back_populates="data",
        lazy="noload",
        cascade="all, delete",
    )

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize to JSON-compatible dictionary.

        Returns
        -------
        dict
            Dictionary with key data fields.
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "extension": self.extension,
            "mimeType": self.mime_type,
            "rawDataLocation": self.processed_path,
            # Use ``to_iso_z`` to emit a single ``Z`` suffix that is well-formed
            # whether the column stored a naive or timezone-aware datetime
            # (issue #116: ``+ "Z"`` produced ``+00:00Z`` on Postgres).
            "createdAt": to_iso_z(self.created_at),
            "updatedAt": to_iso_z(self.updated_at),
            "nodeSet": self.graph_scope,
            "dataSize": self.data_size,
            "tokenCount": self.token_count,
            "pipelineStatus": self.workflow_state,
        }
