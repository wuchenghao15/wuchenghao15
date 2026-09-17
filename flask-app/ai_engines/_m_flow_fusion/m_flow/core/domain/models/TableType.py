"""
Table type descriptor for structured-data ingestion.

Defines the schema used to represent table-level metadata (e.g. a
spreadsheet sheet name or a database table) within the knowledge graph.
Instances are indexed by their ``name`` field to allow fast look-ups
during downstream query processing.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import Field

from m_flow.core import MemoryNode

# Indexing configuration – only the ``name`` field is searchable by default
_TABLE_TYPE_INDEX: Dict[str, Any] = {"index_fields": ["name"]}


class TableType(MemoryNode):
    """
    Represents the schema or category of a data table.

    A *TableType* acts as a grouping label that ties multiple
    :class:`TableRow` instances together under a common schema
    definition.  It stores a human-readable ``name`` (often the
    original table or sheet title) and a ``description`` summarising
    the kind of data the table contains.

    Example::

        tt = TableType(
            name="quarterly_sales",
            description="Regional sales figures broken down by quarter",
        )
    """

    name: str = Field(
        ...,
        description="Human-readable label for the table or sheet",
    )
    description: str = Field(
        ...,
        description="Brief summary of the table's purpose or contents",
    )

    # Declares which fields are forwarded to vector / search indexing
    metadata: dict = Field(default_factory=lambda: dict(_TABLE_TYPE_INDEX))
