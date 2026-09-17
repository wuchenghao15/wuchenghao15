"""
Low-level building blocks for advanced M-flow usage.

Typical consumers are pipeline authors who need direct access to the
graph engine's node type or the one-time database bootstrap routine.

Quick start::

    from m_flow.low_level import MemoryNode, setup

    class MyNode(MemoryNode):
        label: str

    await setup()
"""

from __future__ import annotations

from m_flow.core import ExtendableMemoryNode as MemoryNode
from m_flow.core.domain.operations.setup import setup

__all__: list[str] = ["MemoryNode", "setup"]
