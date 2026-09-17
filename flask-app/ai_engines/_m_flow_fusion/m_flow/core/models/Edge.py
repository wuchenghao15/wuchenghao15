from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_validator


class Edge(BaseModel):
    """Carries optional metadata on a graph relationship between two nodes.

    When annotating typed relationships on a :class:`MemoryNode` subclass,
    wrap the target type together with an ``Edge`` instance::

        related_items: tuple[Edge, list[Item]]
    """

    weight: float | None = None
    weights: dict[str, float] | None = None
    relationship_type: str | None = None
    properties: dict[str, Any] | None = None
    edge_text: str | None = None

    # ------------------------------------------------------------------
    # Use a model-level validator instead of a field-level one so that
    # cross-field defaulting is expressed as a single pre-processing step.
    # ------------------------------------------------------------------

    @model_validator(mode="before")
    @classmethod
    def _populate_defaults(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Fill *edge_text* from *relationship_type* when not supplied."""
        if isinstance(values, dict):
            if values.get("edge_text") is None and values.get("relationship_type"):
                values["edge_text"] = values["relationship_type"]
        return values
