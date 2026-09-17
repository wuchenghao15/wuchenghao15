"""
Classification label for domain entities in the knowledge graph.

A :class:`EntityType` groups related :class:`Entity` instances under
a shared categorical heading (e.g. *"Person"*, *"Organisation"*),
enabling schema-aware queries and faceted browsing of the graph.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import Field

from m_flow.core import MemoryNode

# Indexing configuration – the label is the searchable field
_ENTITY_TYPE_INDEX: Dict[str, Any] = {"index_fields": ["name"]}


class EntityType(MemoryNode):
    """
    Categorical label that classifies entities within the knowledge graph.

    Each instance carries a human-readable ``name`` and a ``description``
    that elaborates on what kinds of entities fall under this type.

    Example::

        et = EntityType(
            name="Organisation",
            description="Legal entities such as companies, NGOs, and agencies",
        )
    """

    name: str = Field(
        ...,
        description="Short label for the entity category",
    )
    description: str = Field(
        ...,
        description="Detailed explanation of what this entity type encompasses",
    )

    # Declares which fields are forwarded to the vector-search index
    metadata: dict = Field(default_factory=lambda: dict(_ENTITY_TYPE_INDEX))


# Backward compatibility alias
