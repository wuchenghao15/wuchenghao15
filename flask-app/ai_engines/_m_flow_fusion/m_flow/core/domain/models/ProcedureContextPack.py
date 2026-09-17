"""
Procedural Memory: ContextPack Model

ContextPack is a container for context information (when/why/boundary/etc.).
This is the middle layer node - CONTAINER ONLY, does NOT participate in retrieval.

Design principles:
- anchor_text: Structured when/why/boundary/outcome/prereq/exception (stored but not indexed)
- Points (ContextPoint) are indexed for fine-grained retrieval
- Retrieval triplet: (Procedure → edge_text → ContextPoint)
"""

from typing import Optional, List

from m_flow.core import MemoryNode


class ProcedureContextPack(MemoryNode):
    """
    Procedural ContextPack (container).

    ContextPack is a CONTAINER ONLY - does NOT participate in retrieval.
    Contains procedure's context information:
    - when: Trigger conditions
    - why: Reasons/motivations
    - boundary: Boundaries/limitations
    - outcome: Expected results
    - prereq: Prerequisites
    - exception: Exception cases

    Attributes:
        name: Used for graph database Node.name
        search_text: Not indexed (kept for compatibility)
        anchor_text: Structured context information (stored but not indexed)
        when_text/why_text/etc.: Structured fields for each context dimension
        has_point: ContextPack -> ContextPoint relationship
    """

    # Used for graph database Node.name
    name: str

    # Not indexed (kept for compatibility, container only)
    search_text: Optional[str] = None

    # Structured context information (stored but not indexed)
    anchor_text: str

    # Full description (not indexed)
    description: Optional[str] = None

    # Structured fields - store each context dimension separately
    when_text: Optional[str] = None  # Trigger conditions
    why_text: Optional[str] = None  # Reasons/motivations
    boundary_text: Optional[str] = None  # Boundaries/limitations
    outcome_text: Optional[str] = None  # Expected results
    prereq_text: Optional[str] = None  # Prerequisites
    exception_text: Optional[str] = None  # Exception cases

    # ContextPack -> ContextPoint relationship
    # Format: List[tuple[Edge, ProcedureContextPoint]]
    has_point: Optional[List] = None  # Type deferred to avoid circular import

    # No index fields - container only, does NOT participate in retrieval
    metadata: dict = {"index_fields": []}
