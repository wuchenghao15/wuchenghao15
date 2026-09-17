"""
M-Flow vector-collection configuration descriptor.

Wraps the low-level ``VectorConfig`` in a higher-level model that
represents a single named embedding collection within the vector store.
"""

from __future__ import annotations

from pydantic import BaseModel

from .VectorConfig import VectorConfig


class CollectionConfig(BaseModel):
    """Describes the storage parameters of one vector collection."""

    vector_config: VectorConfig
