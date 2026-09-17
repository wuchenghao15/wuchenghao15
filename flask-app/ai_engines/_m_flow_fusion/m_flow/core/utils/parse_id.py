"""
Utility for parsing string identifiers into UUIDs.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID


def parse_id(id: Any) -> Any:
    """
    Convert a string to UUID if valid, otherwise return unchanged.

    Parameters
    ----------
    id
        Input value of any type.

    Returns
    -------
    UUID if conversion succeeds, otherwise the original value.
    """
    if not isinstance(id, str):
        return id
    try:
        return UUID(id)
    except (ValueError, AttributeError):
        return id
