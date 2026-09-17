"""
Procedural Memory: KeyPoint Model (formerly StepPoint)

KeyPoint is a fine-grained anchor point under KeyPointsPack, used for precise matching.
This is the tip node of the retrieval triplet structure.

Design principles:
- search_text: Short, specific, contains key anchor for retrieval
- Fine-grained query hits KeyPoint -> pulls up Procedure via edge_text
- Retrieval triplet: (Procedure → edge_text → KeyPoint)
"""

from typing import Optional, List

from m_flow.core import MemoryNode


class ProcedureStepPoint(MemoryNode):
    """
    Fine-grained key point (formerly StepPoint).

    Represents a single step, preference item, habit pattern, or persona trait.
    Can be:
    - Independently vectorized and retrieved
    - Independently scored and explained
    - Independently linked to evidence

    Attributes:
        name: For graph database Node.name
        search_text: Short sentence handle (INDEXED for retrieval)
        description: Explanatory expansion (not indexed)
        point_index: Point index/number (optional)
        supported_by: Evidence links
    """

    # Graph readability: recommend name = search_text
    name: str

    # Main retrieval handle (short, sharp) - INDEXED
    search_text: str

    # Optional: explanatory expansion (for RAG, not indexed)
    description: Optional[str] = None

    # Optional: point index/number
    point_index: Optional[int] = None

    # Optional: evidence links (pointing to ContentFragment)
    supported_by: Optional[List] = None

    # Index fields - only search_text participates in retrieval
    metadata: dict = {"index_fields": ["search_text"]}
