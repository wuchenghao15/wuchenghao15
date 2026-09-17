"""
Core memory node model with versioning and embedding support.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import TypedDict


def _now_ms() -> int:
    """Current UTC time as milliseconds since epoch."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


class NodeMeta(TypedDict):
    """Describes the node's concrete type and which fields are vector-indexed."""

    type: str
    index_fields: List[str]


class MemoryNode(BaseModel):
    """
    Versioned graph node with embedding and serialisation helpers.

    Every domain entity stored in the M-Flow knowledge graph derives from
    this base.  The ``type`` field is auto-populated from the concrete
    subclass name via a Pydantic model validator.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID = Field(default_factory=uuid4)
    type: str = Field(default="MemoryNode")
    version: int = 1
    metadata: Optional[NodeMeta] = Field(default_factory=lambda: {"type": "MemoryNode", "index_fields": []})
    schema_aligned: bool = False
    graph_depth: Optional[int] = 0
    memory_spaces: Optional[List["MemoryNode"]] = Field(
        default=None,
        description="MemorySpace partitions this node belongs to (for subgraph isolation).",
    )
    created_at: int = Field(default_factory=_now_ms)
    updated_at: int = Field(default_factory=_now_ms)

    mentioned_time_start_ms: Optional[int] = None
    mentioned_time_end_ms: Optional[int] = None
    mentioned_time_confidence: Optional[float] = None
    mentioned_time_text: Optional[str] = None

    @model_validator(mode="after")
    def _stamp_type_from_class(self) -> "MemoryNode":
        """Set ``type`` to the concrete class name after construction."""
        self.type = self.__class__.__name__
        return self

    # -- embedding helpers ----------------------------------------------------

    @classmethod
    def extract_index_text(cls, node: "MemoryNode") -> Optional[str]:
        """
        Concatenate index fields into a single string for embedding.

        Returns ``None`` if no index fields are populated.
        """
        meta = node.metadata
        if not meta or not meta.get("index_fields"):
            return None

        parts: List[str] = []
        for fname in meta["index_fields"]:
            val = getattr(node, fname, None)
            if val is None:
                continue
            txt = str(val).strip() if isinstance(val, str) else str(val)
            if txt:
                parts.append(txt)

        return " | ".join(parts) if parts else None

    @classmethod
    def index_field_values(cls, node: "MemoryNode") -> List[Any]:
        """Return a list of values for the node's index fields."""
        meta = node.metadata
        if not meta or not meta.get("index_fields"):
            return []
        return [getattr(node, f, None) for f in meta["index_fields"]]

    @classmethod
    def index_field_names(cls, node: "MemoryNode") -> List[str]:
        """Return the names of the node's index fields."""
        meta = node.metadata
        return list(meta.get("index_fields", [])) if meta else []

    # -- versioning -----------------------------------------------------------

    def bump(self) -> None:
        """Advance to the next revision, recording the current timestamp."""
        now = _now_ms()
        self.version, self.updated_at = self.version + 1, now
