"""Node UUID extraction utility."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID


def extract_uuid_from_node(node: Any) -> Optional[UUID]:
    """
    Extract UUID from a node's id or attributes.

    Returns None if no valid UUID found.
    """
    id_val = getattr(node, "id", None)

    if id_val is None and hasattr(node, "attributes"):
        id_val = node.attributes.get("id")

    if isinstance(id_val, str):
        return UUID(id_val)
    return None
