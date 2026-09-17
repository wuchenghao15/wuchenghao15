"""
Data serialization for pgvector storage.

Converts Python objects to JSON-serializable formats suitable
for storage in PostgreSQL with pgvector extension.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID


def _serialize_value(value: Any) -> Any:
    """Convert a single value to its serializable form."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def serialize_data(data: Any) -> Any:
    """
    Recursively serialize data for database storage.

    Converts datetime objects to ISO 8601 strings and UUIDs
    to their string representation. Handles nested dictionaries
    and lists.

    Args:
        data: Input data structure to serialize.

    Returns:
        Serialized data with all types converted to JSON-compatible formats.

    Example:
        >>> from uuid import uuid4
        >>> from datetime import datetime
        >>> data = {"id": uuid4(), "created": datetime.now()}
        >>> result = serialize_data(data)
        >>> isinstance(result["id"], str)
        True
    """
    if isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items()}

    if isinstance(data, list):
        return [serialize_data(item) for item in data]

    return _serialize_value(data)
