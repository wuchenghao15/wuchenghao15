"""
Core engine utilities package.

This module aggregates low-level helpers that support the engine layer.
All public utilities should be imported directly from this package.

Example usage::

    from m_flow.core.utils import parse_id

    node_id = parse_id("node:abc123")
"""

# Re-exported utilities
from m_flow.core.utils.parse_id import parse_id as parse_id

# Public interface
__all__: list[str] = ["parse_id"]
