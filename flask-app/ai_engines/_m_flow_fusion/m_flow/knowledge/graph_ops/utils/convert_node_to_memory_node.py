"""Hydrate a :class:`MemoryNode` subclass from a raw property dictionary.

The ``type`` key in *node_data* is resolved to the matching Python class via
a recursive walk of all registered :class:`MemoryNode` descendants.
"""

from __future__ import annotations

from typing import Optional, Type

from m_flow.core import MemoryNode

_subclass_cache: dict[str, Type[MemoryNode]] = {}


def _rebuild_cache() -> None:
    """Walk the full MemoryNode hierarchy and cache by class name."""
    _subclass_cache.clear()
    queue = list(MemoryNode.__subclasses__())
    while queue:
        cls = queue.pop()
        _subclass_cache[cls.__name__] = cls
        queue.extend(cls.__subclasses__())


def _resolve_type(type_name: str) -> Optional[Type[MemoryNode]]:
    if type_name not in _subclass_cache:
        _rebuild_cache()
    return _subclass_cache.get(type_name)


def get_all_subclasses(cls: type) -> list[type]:
    """Return every descendant of *cls* (breadth-first)."""
    result: list[type] = []
    queue = list(cls.__subclasses__())
    while queue:
        sub = queue.pop()
        result.append(sub)
        queue.extend(sub.__subclasses__())
    return result


def convert_node_to_memory_node(node_data: dict) -> MemoryNode:
    """Instantiate the correct MemoryNode subclass from a dict with a ``type`` key."""
    cls = _resolve_type(node_data["type"])
    if cls is None:
        raise ValueError(f"Unknown MemoryNode type: {node_data['type']}")
    return cls(**node_data)
