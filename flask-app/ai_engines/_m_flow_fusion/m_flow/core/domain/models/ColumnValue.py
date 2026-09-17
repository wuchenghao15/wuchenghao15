"""
Structured column value representation for tabular data ingestion.

This module defines the schema for individual column values extracted
from structured data sources such as spreadsheets or databases.
Each ColumnValue captures one field entry along with its metadata
for downstream vector indexing.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import Field

from m_flow.core import MemoryNode


# Default configuration that controls which fields are indexed for search
_INDEX_FIELDS_CONFIG: Dict[str, Any] = {"index_fields": ["properties"]}


class ColumnValue(MemoryNode):
    """
    Schema for a single column value extracted from a structured data source.

    Each instance captures the column header (``name``), a human-readable
    explanation (``description``), and the serialized cell content (``properties``).
    The *properties* field is marked for vector indexing by default so that
    downstream search pipelines can locate relevant column values efficiently.

    Example::

        cv = ColumnValue(
            name="revenue",
            description="Annual revenue in USD",
            properties="1500000",
        )
    """

    name: str = Field(
        ...,
        description="Column header or field identifier from the source table",
    )
    description: str = Field(
        ...,
        description="Human-readable explanation of what this column represents",
    )
    properties: str = Field(
        ...,
        description="Serialized cell content for this column entry",
    )

    # Controls which fields participate in vector / search indexing
    metadata: dict = Field(default_factory=lambda: dict(_INDEX_FIELDS_CONFIG))
