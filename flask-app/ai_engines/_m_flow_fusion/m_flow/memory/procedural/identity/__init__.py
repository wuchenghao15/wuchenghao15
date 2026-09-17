"""
Identity normalization for procedural memory.

This module provides utilities for normalizing entity identities,
managing aliases, and deduplicating procedural memory entries.

Components:

- :func:`normalize_identity` - Main entry point for identity normalization
- :class:`IdentityResult` - Container for normalization results
- :class:`IdentityNormalizer` - Configurable identity processor

Example::

    from m_flow.memory.procedural.identity import normalize_identity

    result = normalize_identity(raw_entity)
"""

from m_flow.memory.procedural.identity.normalize_identity import (
    normalize_identity as normalize_identity,
    IdentityResult as IdentityResult,
    IdentityNormalizer as IdentityNormalizer,
)

__all__: list[str] = [
    "normalize_identity",
    "IdentityResult",
    "IdentityNormalizer",
]
