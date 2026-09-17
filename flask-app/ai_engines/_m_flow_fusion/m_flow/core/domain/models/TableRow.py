"""
Single-row representation extracted from a structured data table.

Each :class:`TableRow` captures one record (row) from a data source,
preserving the row's identifier, a textual summary, and a serialised
blob of the cell values.  The ``properties`` field is indexed for
full-text and vector search so that individual rows can be retrieved
by content during graph construction.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import Field

from m_flow.core import MemoryNode

# Default search-indexing configuration for row instances
_ROW_INDEX_FIELDS: Dict[str, Any] = {"index_fields": ["properties"]}


class TableRow(MemoryNode):
    """
    Represents a single row extracted from a structured data source.

    A *TableRow* stores the row's label (``name``), a human-readable
    ``description`` of what the row contains, and a ``properties``
    string that holds the serialised cell values.  The properties
    blob is the primary field used for embedding and retrieval.

    Example::

        row = TableRow(
            name="row_42",
            description="Sales record for Q3 2025",
            properties='{"region": "EMEA", "revenue": 150000}',
        )
    """

    name: str = Field(
        ...,
        description="Identifier or label for this row within its parent table",
    )
    description: str = Field(
        ...,
        description="Textual summary describing the row's contents",
    )
    properties: str = Field(
        ...,
        description="Serialised cell values for embedding and retrieval",
    )

    # Controls which fields the indexing pipeline processes
    metadata: dict = Field(default_factory=lambda: dict(_ROW_INDEX_FIELDS))
