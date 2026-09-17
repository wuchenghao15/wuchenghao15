"""
Episode model enhancements.

New additions:
- includes_chunk: Episode → ContentFragment evidence mounting edges (optional)
"""

from typing import List, Optional

from m_flow.core import MemoryNode, Edge
from m_flow.core.domain.models.Entity import Entity  # Entity is new name, Entity is alias
from m_flow.core.domain.models.Facet import Facet


class Episode(MemoryNode):
    """
    Episodic Episode (anchor).

    Episode is the anchor for coarse-grained memory, used for information aggregation across multiple ContentFragments.

    Design principles (aligned with brute force triplet search success pattern):
    - summary: Retrieval carrier for episodic anchor (participates in vectorization), analogous to ContentFragment.text
    - has_facet / involves_entity: Write rich semantic edges via Edge(edge_text=...), analogous to contains.edge_text

    Typical triple structure (aligned with "whole - rich semantic link edge - detail" pattern):
    1. Episode (anchor) --[edge_text]--> Facet (detail)
    2. Episode (anchor) --[edge_text]--> Entity (detail)

    Enhancements:
    - includes_chunk: Episode → ContentFragment evidence mounting edges (not participating in episodic retrieval)
    - derived_procedure: Episode → Procedure source tracing edges (for learn() operation to prevent duplicates)

    Attributes:
        name: Used for graph database Node.name (short title)
        summary: Retrievable summary of episode, as main vectorization field
        signature: Optional stable short handle for quick identification
        status: Optional status marker (open/closed/...)
        has_facet: Episode→Facet relationship, using tuple[Edge, Facet] to carry edge_text
        involves_entity: Episode→Entity relationship, using tuple[Edge, Entity] to carry edge_text
        includes_chunk: Episode→ContentFragment evidence mounting edges
        derived_procedure: Episode→Procedure source tracing edges (established by learn() operation)
        size_check_threshold: Personalized threshold for Episode size check (None = use global default)
    """

    # Used for graph database Node.name (short title)
    name: str

    # Anchor: retrievable summary of episode (recommended 200-500 chars)
    # This is the main vectorization field, analogous to ContentFragment.text
    summary: str

    # Optional: shorter stable handle (can add index field later; not indexed initially to avoid multi-field coverage issues)
    signature: Optional[str] = None

    # Optional: status marker (open/closed/...); stored as attribute only, not participating in indexing
    status: Optional[str] = "open"

    # Memory type marker: distinguish Episodic and Atomic Episode
    # - "episodic": Standard event/episode memory (default)
    # - "atomic": Independent atomic-level knowledge fragment, goes through full Episode flow but essentially single fact
    # Used to distinguish different types of memory during retrieval
    memory_type: Optional[str] = None  # "episodic" | "atomic" | None

    # Dataset isolation: ID of the dataset this Episode belongs to
    # Used for filtering during Episode Routing to prevent cross-dataset merging
    # when ENABLE_BACKEND_ACCESS_CONTROL=false (shared database mode)
    dataset_id: Optional[str] = None

    # Display-only field: NOT indexed, but displayed when the node is retrieved
    # This field is not populated by standard ingestion pipelines.
    # Users can manually set this field to add additional context/notes that will be shown
    # when this Episode is retrieved, without affecting search/retrieval behavior.
    display_only: Optional[str] = None

    # Typical triple 1: episode anchor --[edge_text]--> facet
    # Uses tuple[Edge, Facet] format, Edge.edge_text will be written to edge attributes by extract_graph
    # Then extracted to RelationType_relationship_name collection by index_relations
    has_facet: Optional[List[tuple[Edge, Facet]]] = None

    # Typical triple 2: episode anchor --[edge_text]--> entity
    # Uses tuple[Edge, Entity] format, aligned with ContentFragment.contains writing style
    involves_entity: Optional[List[tuple[Edge, Entity]]] = None

    # Episode → ContentFragment evidence mounting edges (optional)
    # Format: List[tuple[Edge, ContentFragment]]
    # These edges don't participate in episodic retrieval, but support subsequent RAG precise evidence retrieval
    includes_chunk: Optional[List] = None  # Type deferred to avoid circular import

    # Episode → Procedure source tracing edges (optional)
    # When learn() operation extracts Procedural Memory from this Episode, establish this edge
    # Used to prevent duplicate processing (fetch_episodes_from_graph will exclude Episodes with this edge)
    # Format: List[tuple[Edge, Procedure]]
    derived_procedure: Optional[List] = None  # Type deferred to avoid circular import

    # Episode Size Check: personalized trigger threshold
    # When LLM judges this Episode as reasonable despite being large,
    # this threshold is set to (current_facet_count + margin).
    # Next size check only triggers when facet_count > this threshold.
    # None = use global default threshold
    size_check_threshold: Optional[int] = None

    # Only index summary (ensure "one node one collection", retrieval can initially equal-weight copy bruteforce)
    # This way Episode_summary collection is analogous to ContentFragment_text collection
    metadata: dict = {"index_fields": ["summary"]}
