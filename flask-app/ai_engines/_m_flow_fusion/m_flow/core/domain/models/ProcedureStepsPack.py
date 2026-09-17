"""
Procedural Memory: KeyPointsPack Model (formerly StepsPack)

KeyPointsPack is a container for key points (steps for processes, bullet points for preferences/persona).
This is the middle layer node - CONTAINER ONLY, does NOT participate in retrieval.

Design principles:
- anchor_text: Complete points text (stored but not indexed)
- Points (KeyPoint) are indexed for fine-grained retrieval
- Retrieval triplet: (Procedure → edge_text → KeyPoint)
"""

from typing import Optional, List

from m_flow.core import MemoryNode


class ProcedureStepsPack(MemoryNode):
    """
    Procedural KeyPointsPack (container, formerly StepsPack).

    KeyPointsPack is a CONTAINER ONLY - does NOT participate in retrieval.
    Contains procedure's key points:
    - Steps for reusable_process type
    - Bullet points for user_preference/persona/habit types

    Attributes:
        name: For graph database Node.name
        search_text: Not indexed (kept for compatibility)
        anchor_text: Complete points text (stored but not indexed)
        has_point: KeyPointsPack -> KeyPoint relationship
    """

    # For graph database Node.name
    name: str

    # Not indexed (kept for compatibility, container only)
    search_text: Optional[str] = None

    # Complete points text (stored but not indexed)
    anchor_text: str

    # Complete description (not indexed)
    description: Optional[str] = None

    # KeyPointsPack -> KeyPoint relationship
    # Format: List[tuple[Edge, ProcedureStepPoint]]
    has_point: Optional[List] = None  # Type deferred to avoid circular import

    # No index fields - container only, does NOT participate in retrieval
    metadata: dict = {"index_fields": []}
