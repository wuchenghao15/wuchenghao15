from __future__ import annotations
from m_flow.core import MemoryNode, Edge
from m_flow.core.domain.models.EntityType import EntityType
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Entity(MemoryNode):
    """
    Entity represents an atomic entity (name, number, date, tool, person, etc.)
    extracted from text.

    Design for cross-event entity management:
    - Each Entity instance is unique per (entity_name, context/episode).
    - `canonical_name` is used for normalized matching (optional).
    - `same_entity_as` edges link entities with the same canonical_name for discovery.

    Attributes:
        name: The entity name as it appears in text
        description: Context-specific description (what this entity means in this episode)
        canonical_name: Normalized name for cross-episode matching
        memory_type: Memory type marker ("atomic" | "episodic" | None for legacy)
        same_entity_as: Links to other Entity nodes with the same canonical_name
    """

    name: str
    is_a: Optional[EntityType] = None
    description: str

    # Canonical name for cross-event entity matching (normalized, lowercase, no spaces)
    # All entities with the same canonical_name are considered "the same entity"
    canonical_name: Optional[str] = None

    # Memory type marker for retrieval filtering
    # "atomic": Entity from Atomic Episode (inherits Episode.memory_type="atomic")
    # "episodic": Entity from Episodic Episode (inherits Episode.memory_type="episodic")
    # None: will not be filtered by memory_type
    # Note: Both atomic and episodic entities now use Episode → Entity via involves_entity edge
    memory_type: Optional[str] = None

    # Cross-episode entity linking: Entity → Entity (same canonical_name)
    # Uses tuple[Edge, Entity] format, same as Episode.involves_entity
    # The edge_text contains both entities' descriptions for discovery
    same_entity_as: Optional[List[tuple[Edge, "Entity"]]] = None

    # Merge tracking: number of times this entity's description has been merged
    # Used to identify entities that may benefit from LLM description optimization
    merge_count: int = 0

    # Display-only field: NOT indexed, but displayed when the node is retrieved
    # This field is not populated by standard ingestion pipelines.
    # Users can manually set this field to add additional context/notes that will be shown
    # when this Entity is retrieved, without affecting search/retrieval behavior.
    display_only: Optional[str] = None

    metadata: dict = {"index_fields": ["name", "canonical_name"]}


# Backward compatibility alias
