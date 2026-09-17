"""Memory-graph nodes that capture relational-database schema topology."""

from __future__ import annotations

from typing import Optional

from m_flow.core.models.MemoryNode import MemoryNode


class DatabaseSchema(MemoryNode):
    """Top-level container describing an entire database's structure.

    Stores a textual summary of every table together with a limited set
    of representative sample rows so that downstream LLM tasks can
    reason about the schema without direct DB access.
    """

    name: str
    database_type: str
    tables: str
    sample_data: str
    description: str
    metadata: dict = {"index_fields": ["description", "name"]}


class SchemaTable(MemoryNode):
    """Single-table descriptor within a :class:`DatabaseSchema`.

    Captures column definitions, key constraints, and a handful of
    example rows.  ``row_count_estimate`` is advisory — it may be
    ``None`` when statistics are unavailable.
    """

    name: str
    columns: str
    primary_key: Optional[str] = None
    foreign_keys: str
    sample_rows: str
    row_count_estimate: Optional[int] = None
    description: str
    metadata: dict = {"index_fields": ["description", "name"]}


class SchemaRelationship(MemoryNode):
    """Directed edge connecting two :class:`SchemaTable` nodes.

    Encodes a foreign-key or logical join relationship that the
    ingestion pipeline discovered when inspecting the source database.
    """

    name: str
    source_table: str
    target_table: str
    relationship_type: str
    source_column: str
    target_column: str
    description: str
    metadata: dict = {"index_fields": ["description", "name"]}
