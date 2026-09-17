"""Pydantic model utilities for the storage layer.

Provides helpers to:
* serialise complex Python objects to JSON,
* create lightweight copies of MemoryNode schemas, and
* extract flat (non-nested) field values from node instances.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field, create_model

from m_flow.core import MemoryNode

# ---------------------------------------------------------------------------
# JSON serialisation
# ---------------------------------------------------------------------------

# Dispatch table: type → converter function
_SERIALISERS: Dict[type, Any] = {}


def _register_serialiser(tp: type, fn):
    """Register a converter for a specific type."""
    _SERIALISERS[tp] = fn


def _init_serialisers():
    """Populate the default converter table (called once at import time)."""
    import datetime as _dt
    from decimal import Decimal as _Dec
    from uuid import UUID as _UUID

    _register_serialiser(_dt.datetime, lambda o: o.isoformat())
    _register_serialiser(_UUID, str)
    _register_serialiser(_Dec, float)


_init_serialisers()


class JSONEncoder(json.JSONEncoder):
    """Extended encoder that handles ``datetime``, ``UUID`` and ``Decimal``."""

    def default(self, o: Any) -> Any:  # noqa: D401
        converter = _SERIALISERS.get(type(o))
        if converter is not None:
            return converter(o)
        if hasattr(o, "hex"):
            return str(o)
        return super().default(o)


# ---------------------------------------------------------------------------
# Model copying
# ---------------------------------------------------------------------------


def _resolve_field_default(field_info):
    """Return (annotation, default_or_Field) suitable for ``create_model``."""
    if field_info.default_factory is not None:
        return field_info.annotation, Field(default_factory=field_info.default_factory)
    return field_info.annotation, field_info.default


def copy_model(
    model: Type[MemoryNode],
    include_fields: Optional[Dict[str, Any]] = None,
    exclude_fields: Optional[List[str]] = None,
) -> Type[BaseModel]:
    """Derive a new Pydantic model from *model*, optionally adding or dropping fields.

    The returned model is registered as a virtual subclass of ``MemoryNode``
    so ``isinstance`` checks continue to work.
    """
    include_fields = include_fields or {}
    exclude_fields = set(exclude_fields or [])

    collected: Dict[str, Any] = {
        name: _resolve_field_default(info) for name, info in model.model_fields.items() if name not in exclude_fields
    }
    collected.update(include_fields)

    class _Configured(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

    derived = create_model(model.__name__, __base__=_Configured, **collected)
    derived.model_rebuild()

    # Allow isinstance(instance, MemoryNode) to return True
    MemoryNode.register(derived)
    return derived


# ---------------------------------------------------------------------------
# Property extraction
# ---------------------------------------------------------------------------

_SKIP_FIELDS = frozenset({"metadata"})


def get_own_properties(memory_node: MemoryNode) -> Dict[str, Any]:
    """Return the flat (scalar / list-of-scalars) properties of *memory_node*.

    Nested ``MemoryNode`` instances and plain ``dict`` values are excluded.
    """
    result: Dict[str, Any] = {}
    for attr_name, attr_val in memory_node:
        if attr_name in _SKIP_FIELDS:
            continue
        if isinstance(attr_val, (dict, MemoryNode)):
            continue
        if isinstance(attr_val, list) and attr_val and isinstance(attr_val[0], MemoryNode):
            continue
        result[attr_name] = attr_val
    return result
