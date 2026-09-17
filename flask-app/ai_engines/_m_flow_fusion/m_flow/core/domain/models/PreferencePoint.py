"""
Preference Memory: PreferencePoint Model

PreferencePoint is the core node for preference memory, used to store simple abstract information:
- User preferences (format, style, habits)
- Behavioral habits (fixed time, location)
- Simple conventions (naming standards, tool choices)
- Rules of thumb (single rule, not multi-step)

Design principles:
- Flat structure: Single node, no child nodes (distinct from Procedure's hierarchical structure)
- Single field indexing: Only index content field (simplified retrieval)
- Independent channel: Separated from Procedure retrieval channel to avoid interference
- Traceable: source_refs + evidence fields support evidence tracing

Differences from Procedure:
| Dimension | Procedure | PreferencePoint |
|-----------|-----------|-----------------|
| Structure | Hierarchical (5-tuple) | Flat (single node) |
| Child nodes | ContextPack + StepsPack + Points | None |
| Indexing | 3 collections | 1 collection |
| Applicable to | Multi-step processes | Simple preferences/habits |
"""

from typing import Optional, List

from m_flow.core import MemoryNode


class PreferencePoint(MemoryNode):
    """
    Preference point: stores simple abstract information (preferences/habits/conventions).

    This is a flat node that contains all information and does not depend on child nodes.

    Attributes:
        name: Short title for UI display (not indexed)
        content: Full description, unique indexed field (50-150 chars)
        category: Category label
        what_to_remember: Core information LLM needs to remember
        when_to_apply: When to apply (optional)
        confidence: Confidence level (high/low)
        status: Status (active/deprecated)
        version: Version number (preferences may evolve)
        source_refs: Source tracing (episode/chunk ID)
        evidence: Original text evidence (direct quote from source)
        updated_at: Last update time

    Indexing strategy:
    - Only index content field
    - Moderate length (50-150 chars): matches both short and long queries

    Retrieval channel:
    - PreferencePoint_content (independent from Procedure channel)
    """

    # ===== Display information =====
    # Short title for UI and log display (not indexed)
    name: str

    # ===== Unique retrieval anchor (participates in vectorization) =====
    # Full description, 50-150 chars
    # Example: "Play ball with colleagues after work, fixed time 6:30, location usual place"
    content: str

    # ===== Classification =====
    # Category label for filtering and analysis
    # Possible values: user_preference | habit | convention | rule |
    #                 tool_usage | format | naming | other
    category: str

    # ===== RAG injection information (not indexed) =====
    # Core information LLM needs to remember
    # Example: "time=6:30, location=usual place"
    what_to_remember: str

    # When to apply (optional)
    # Example: "when discussing after-work activities"
    when_to_apply: Optional[str] = None

    # ===== Metadata =====
    # Confidence: high (explicit preference) / low (inferred preference)
    confidence: str = "high"

    # Status: active / deprecated
    status: str = "active"

    # Version number (preferences may evolve over time)
    version: int = 1

    # ===== Evidence tracing (critical!) =====
    # Source tracing: points to original episode/chunk IDs
    # Format: ["episode:xxx", "chunk:yyy"]
    source_refs: Optional[List[str]] = None

    # Original text evidence: direct quote from source supporting this preference
    # Example: "usual place...6:30"
    evidence: Optional[str] = None

    # Last update time (ISO format)
    updated_at: Optional[str] = None

    # ===== Version management edges (optional) =====
    # PreferencePoint --(supersedes)--> PreferencePoint
    # Used when new preference replaces old preference
    supersedes: Optional[List] = None  # List[Tuple[Edge, PreferencePoint]]

    # ===== Index configuration =====
    # Only index content field, forming independent retrieval channel
    metadata: dict = {"index_fields": ["content"]}
