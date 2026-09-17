"""
Vector search hit model.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class VectorSearchHit(BaseModel):
    """
    Single hit returned by a vector similarity search.

    Attributes:
        id: Unique result identifier.
        score: Normalized score [0,1], lower is better.
        payload: Associated metadata.
        raw_distance: Raw vector distance.
        collection_name: Source collection name.
    """

    id: UUID
    score: float = Field(ge=0.0, le=1.0)
    payload: dict[str, Any]
    raw_distance: float | None = Field(default=None, ge=0.0)
    collection_name: str | None = None

    model_config = {"extra": "allow"}

    @field_validator("raw_distance")
    @classmethod
    def check_raw_distance(cls, val: float | None) -> float | None:
        """Ensure raw distance is non-negative."""
        if val is not None and val < 0:
            raise ValueError("raw_distance must be non-negative")
        return val

    def debug_str(self) -> str:
        """Return a debug-friendly string representation."""
        return (
            f"VectorSearchHit(id={str(self.id)[:8]}..., "
            f"score={self.score:.4f}, "
            f"raw={self.raw_distance}, "
            f"coll={self.collection_name})"
        )


# Backward-compatible alias
