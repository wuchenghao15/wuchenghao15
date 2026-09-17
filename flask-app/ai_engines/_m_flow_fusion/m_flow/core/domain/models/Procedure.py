"""
Procedural Memory: Procedure Model

Procedure is the top-level anchor for procedural memory, representing a reusable method/step/process.

Retrieval triplet structure (no intermediate Pack nodes):
- Procedure (anchor) → has_context_point → ContextPoint
- Procedure (anchor) → has_key_point → KeyPoint (ProcedureStepPoint)

Design principles:
- summary: Only indexed field, contains search_text + context + key_points
- context_text / points_text: Non-indexed display attributes (for ProcedureCard rendering)
- Points are indexed for fine-grained retrieval via search_text
- Retrieval triplet: (Procedure → edge_text → Point)
"""

from typing import Optional, List

from m_flow.core import MemoryNode


class Procedure(MemoryNode):
    """
    Procedural Procedure (anchor).

    Procedure is the top-level anchor for procedural memory, used to store reusable methods/steps/processes.

    Retrieval triplet structure:
    - Procedure → has_context_point → ContextPoint (direct, no Pack)
    - Procedure → has_key_point → KeyPoint (direct, no Pack)

    Attributes:
        name: Used for graph database Node.name (short title)
        summary: Only indexed field, contains search_text + context + key_points
        search_text: Short handle (embedded in summary, not separately indexed)
        context_text: Non-indexed display text for context (replaces ContextPack.anchor_text)
        points_text: Non-indexed display text for key points (replaces StepsPack.anchor_text)
        signature: Stable short handle for version management
        version: Version number for incremental updates
        status: Status marker (active/deprecated)
        confidence: Confidence marker (high/low) for soft filtering
        has_context_point: Procedure -> ContextPoint relationship (direct)
        has_key_point: Procedure -> KeyPoint relationship (direct)
    """

    # Used for graph database Node.name (short title)
    name: str

    # Anchor: retrievable summary of procedure (ONLY indexed field)
    # Contains search_text + context + key_points combined
    summary: str

    # Short sentence handle (embedded in summary, not separately indexed)
    search_text: str

    # Non-indexed display attributes (for ProcedureCard rendering)
    # Display-only text fields (not indexed)
    context_text: Optional[str] = None  # Complete context text (When/Why/Boundary/...)
    points_text: Optional[str] = None  # Complete key points text (steps/preferences/habits)

    # Stable short handle for version management
    signature: Optional[str] = None

    # Version number for incremental updates
    version: int = 1

    # Status marker (active/deprecated/superseded)
    status: str = "active"

    # Version management auxiliary fields
    # Source tracing (which episodes/chunks this update came from)
    source_refs: Optional[List[str]] = None

    # Update time (ISO string)
    updated_at: Optional[str] = None

    # Confidence marker (high/low) for soft filtering
    # Marked as "low" when should_write=maybe, small penalty during retrieval
    confidence: str = "high"

    # Write decision metadata (soft gating)
    # Write decision: yes/maybe/no (from LLM Router)
    write_decision: Optional[str] = None

    # Write reason: why it's worth remembering (traceability)
    write_reason: Optional[str] = None

    # Evidence references: references to source episode/facet/chunk
    # Format: ["episode:xxx", "facet:yyy", "chunk:zzz"]
    evidence_refs: Optional[List[str]] = None

    # Procedure -> ContextPoint relationship (direct, no Pack intermediate)
    # Format: List[tuple[Edge, ProcedureContextPoint]]
    has_context_point: Optional[List] = None  # Type deferred to avoid circular import

    # Procedure -> KeyPoint relationship (direct, no Pack intermediate)
    # Format: List[tuple[Edge, ProcedureStepPoint]]
    has_key_point: Optional[List] = None  # Type deferred to avoid circular import

    # Version management: supersedes edges (new version -> old version)
    # Format: List[tuple[Edge, Procedure]]
    # For auditing and backtracking: new Procedure supersedes old Procedure
    supersedes: Optional[List] = None  # Type deferred to avoid circular import

    # Index fields:
    # - Procedure_summary: Only indexed field (contains search_text + context + key_points)
    metadata: dict = {"index_fields": ["summary"]}
