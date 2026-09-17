"""
Isolated memory namespace for multi-tenant graph partitioning.

A :class:`MemorySpace` acts as a logical boundary within the knowledge
graph, ensuring that nodes belonging to different tenants or domains
remain separated during queries and indexing operations.
"""

from __future__ import annotations

from pydantic import Field

from m_flow.core import MemoryNode


class MemorySpace(MemoryNode):
    """
    Logical partition that scopes a subset of the knowledge graph.

    Downstream query engines filter results by the space ``name``
    to enforce isolation between different tenants or projects.

    Example::

        space = MemorySpace(name="project_alpha")
    """

    name: str = Field(
        ...,
        description="Unique identifier for this memory partition",
    )
