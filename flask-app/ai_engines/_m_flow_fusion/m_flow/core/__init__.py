"""
M-flow Core Engine Package.

This package provides the foundational data structures for the knowledge graph:

- :class:`MemoryNode` - Base class for all graph nodes
- :class:`ExtendableMemoryNode` - Node type supporting dynamic field extension
- :class:`Edge` - Relationship container connecting nodes

Usage example::

    from m_flow.core import MemoryNode, Edge

    node = MemoryNode(name="example")
    edge = Edge(source_node_id=node.id, target_node_id="other")
"""

# Core model exports
from m_flow.core.models.MemoryNode import MemoryNode as MemoryNode
from m_flow.core.models.ExtendableMemoryNode import (
    ExtendableMemoryNode as ExtendableMemoryNode,
)
from m_flow.core.models.Edge import Edge as Edge

# Public interface definition
__all__: list[str] = [
    "MemoryNode",
    "ExtendableMemoryNode",
    "Edge",
]
