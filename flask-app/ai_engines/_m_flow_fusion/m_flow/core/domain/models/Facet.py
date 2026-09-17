"""
Facet model enhancements.

Historical enhancements:
- aliases: Synonymous/variant handles (structured storage, not directly indexed)
- aliases_text: Concatenated aliases text (participates in vectorization, for fallback recall)
- supported_by: Evidence chunks (structured and traceable, not participating in episodic main retrieval)

Enhancements:
- anchor_text: Middle-layer rich semantic field (participates in vectorization), can directly equal description
- has_point: Fine-grained point collection Facet → FacetPoint
"""

from typing import Optional, List, TYPE_CHECKING

from m_flow.core import MemoryNode

if TYPE_CHECKING:
    pass


class Facet(MemoryNode):
    """
    Episodic Facet (detail handle).

    Facet is the detail anchor for Episode, used for precise positioning in coarse-grained retrieval.

    Design principles (aligned with brute force triplet search success pattern):
    - search_text: Short and sharp retrieval anchor (participates in vectorization), analogous to Entity.name
    - aliases_text: Fallback recall handle (participates in vectorization), 2-5 short synonymous expressions concatenated
    - description: Descriptive text for RAG expansion (not participating in vectorization)

    Enhancements:
    - aliases: Synonymous/variant handles (structured storage, not directly indexed)
    - aliases_text: Result of "\n".join(aliases), participates in vectorization for fallback recall
    - supported_by: Evidence edges Facet → ContentFragment (structured and traceable)

    Attributes:
        name: Used for graph database Node.name (readability/debugging important), recommended name = search_text
        facet_type: Facet type (decision/risk/outcome/metric/issue/plan/constraint/cause...)
        search_text: Main retrieval handle (short, sharp) -> indexed
        aliases: Synonymous/variant handles (structured storage, not directly indexed)
        aliases_text: Fallback recall handle (2-5 short synonymous expressions concatenated) -> indexed
        description: Expansion field (not indexed), used for RAG context expansion
        supported_by: Evidence edges pointing to ContentFragments supporting this facet
    """

    # Used for graph database Node.name (readability/debugging important)
    name: str

    # Facet type: decision / risk / outcome / metric / issue / plan / constraint / cause ...
    facet_type: str

    # Main retrieval handle (short, sharp) - participates in vectorization
    search_text: str

    # Synonymous/variant handles (structured storage, not directly indexed)
    aliases: Optional[List[str]] = None

    # Fallback recall handle (aliases concatenated text) - participates in vectorization
    # Result of "\n".join(aliases), recommended length truncation to 200-300 chars
    aliases_text: Optional[str] = None

    # Expansion field (not indexed) - used for RAG context expansion
    description: Optional[str] = None

    # Display-only field: NOT indexed, but displayed when the node is retrieved
    # This field is not populated by standard ingestion pipelines.
    # Users can manually set this field to add additional context/notes that will be shown
    # when this Facet is retrieved, without affecting search/retrieval behavior.
    display_only: Optional[str] = None

    # Dataset isolation: ID of the dataset this Facet belongs to
    # Used for filtering during Episode Routing to prevent cross-dataset merging
    # when ENABLE_BACKEND_ACCESS_CONTROL=false (shared database mode)
    dataset_id: Optional[str] = None

    # Middle-layer rich semantic field (participates in vectorization)
    # Design intent: For Facet --has_point--> FacetPoint hierarchical layer, making Facet more than just a short handle.
    # You can directly set anchor_text = description (description is already condensed facet), no need for additional summary.
    # Model layer doesn't limit length; if need to adapt to embedding limits, do safe truncation at write/index stage.
    anchor_text: Optional[str] = None

    # Evidence edges Facet → ContentFragment (optional)
    # Format: List[tuple[Edge, ContentFragment]]
    # These edges don't participate in episodic retrieval, but support subsequent RAG precise evidence retrieval
    supported_by: Optional[List] = None  # Type deferred to avoid circular import

    # Fine-grained point collection Facet → FacetPoint
    # Format: List[tuple[Edge, FacetPoint]] or List[FacetPoint]
    # These edges turn facet information points into independently matchable, independently scored, independently linked evidence nodes
    has_point: Optional[List] = None  # Type deferred to avoid circular import

    # Index fields:
    # - Facet_search_text: Main entry (short, sharp)
    # - Facet_anchor_text: Middle-layer rich semantic
    # NOTE: aliases_text not indexed because:
    #   1. Section-based path doesn't generate aliases (coverage only 2.8%)
    #   2. aliases content is just synonyms of titles, doesn't contain specific information
    #   3. Easy to cause false matches (e.g., "Bitcoin price" matches "housing price differentiation")
    metadata: dict = {"index_fields": ["search_text", "anchor_text"]}
