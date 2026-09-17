"""
Extension base class for application-defined memory graph nodes.

Provides :class:`ExtendableMemoryNode`, a thin subclass of
:class:`MemoryNode` that application code should inherit from when
defining domain-specific node types.  Keeping a dedicated base
class allows the framework to distinguish user models from internal
engine models during schema introspection and serialisation.
"""

from __future__ import annotations

from .MemoryNode import MemoryNode


class ExtendableMemoryNode(MemoryNode):
    """
    Base class for domain models that participate in the memory graph.

    Subclass this — rather than :class:`MemoryNode` directly — when you
    need a node type that end-users can extend with custom fields or
    validators.  The framework relies on this marker class to apply
    user-facing schema validation rules and migration logic.

    Concrete subclasses are expected to declare at least a ``name``
    field so that the node can be rendered in graph visualisations.
    """

    pass
