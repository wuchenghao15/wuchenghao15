"""Append-only ledger that records every graph-edge lifecycle event."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_OID, UUID as PyUUID, uuid5

from sqlalchemy import UUID, Column, DateTime, Index, String

from m_flow.adapters.relational import Base


def _mint_ledger_entry_id() -> PyUUID:
    """Derive a deterministic UUID from the current UTC wall-clock."""
    utc_now = datetime.now(tz=timezone.utc)
    return uuid5(NAMESPACE_OID, str(utc_now.timestamp()))


def _utc_timestamp() -> datetime:
    return datetime.now(tz=timezone.utc)


class GraphRelationshipLedger(Base):
    """Immutable audit trail for graph-relationship mutations.

    Every time an edge is created or soft-deleted between two nodes the
    event is persisted here.  The ledger is append-only — rows are never
    updated, only new entries (with ``deleted_at`` populated) are added
    when an edge is removed.

    Attributes
    ----------
    source_node_id : UUID
        Origin vertex of the relationship.
    destination_node_id : UUID
        Target vertex of the relationship.
    creator_function : str
        Fully-qualified name of the function that produced the edge.
    node_label : str | None
        Optional human-readable tag for the edge category.
    """

    __tablename__ = "graph_relationship_ledger"

    id = Column(UUID, primary_key=True, default=_mint_ledger_entry_id)

    source_node_id = Column(UUID, nullable=False)
    destination_node_id = Column(UUID, nullable=False)
    creator_function = Column(String, nullable=False)
    node_label = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utc_timestamp)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(UUID, nullable=True)

    __table_args__ = (
        Index("idx_graph_relationship_id", "id"),
        Index("idx_graph_rel_ledger_src", "source_node_id"),
        Index("idx_graph_rel_ledger_dst", "destination_node_id"),
        {"extend_existing": True},
    )

    def to_json(self) -> dict:
        """Serialise this ledger entry into a plain ``dict``."""
        return {
            "id": str(self.id),
            "source_node_id": str(self.source_node_id),
            "destination_node_id": str(self.destination_node_id),
            "creator_function": self.creator_function,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "deleted_at": (self.deleted_at.isoformat() if self.deleted_at else None),
            "user_id": str(self.user_id) if self.user_id else None,
        }
