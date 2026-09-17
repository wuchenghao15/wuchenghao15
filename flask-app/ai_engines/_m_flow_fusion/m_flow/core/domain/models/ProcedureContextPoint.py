"""
Procedural memory context point model.

ContextPoint is a fine-grained anchor for matching trigger conditions
and boundary constraints within a ContextPack hierarchy.

Design principles:
- search_text: Short, specific, contains key anchor for retrieval
- Fine-grained query hits ContextPoint -> pulls up Procedure via edge_text
- Retrieval triplet: (Procedure → edge_text → ContextPoint)
"""

from __future__ import annotations

from typing import Any, List, Optional

from m_flow.core import MemoryNode


class ProcedureContextPoint(MemoryNode):
    """
    Fine-grained context point for procedural retrieval.

    Represents a single trigger condition, boundary, or context constraint.
    Can be:
    - Independently vectorized and retrieved
    - Independently scored and explained
    - Independently linked to evidence

    Attributes:
        name: For graph database Node.name
        search_text: Short sentence handle (INDEXED for retrieval)
        description: Explanatory expansion (not indexed)
        point_type: Type of context point (when/why/boundary/outcome/prereq/exception)
        supported_by: Evidence links
    """

    name: str
    search_text: str
    description: Optional[str] = None
    point_type: Optional[str] = None
    supported_by: Optional[List[Any]] = None

    # Index fields - only search_text participates in retrieval
    metadata: dict = {"index_fields": ["search_text"]}
