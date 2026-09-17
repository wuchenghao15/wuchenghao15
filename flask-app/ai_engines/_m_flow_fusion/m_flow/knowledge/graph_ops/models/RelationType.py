"""Relation type model for graph edges."""

from __future__ import annotations


from m_flow.core import MemoryNode


class RelationType(MemoryNode):
    """Aggregated statistics for a relationship type."""

    relationship_name: str
    number_of_edges: int

    metadata: dict = {"index_fields": ["relationship_name"]}
