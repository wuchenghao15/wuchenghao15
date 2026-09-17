"""
Community retriever registration for M-flow.

Maintains a registry of community-contributed retrieval
implementations that can be dynamically loaded.
"""

from __future__ import annotations

from typing import Any, Dict

# Global registry for community-contributed retrievers
# Format: {"retriever_name": RetrieverClass}
registered_community_retrievers: Dict[str, Any] = {}


def register_community_retriever(name: str, retriever_class: Any) -> None:
    """Register a community retriever implementation."""
    registered_community_retrievers[name] = retriever_class


def get_community_retriever(name: str) -> Any:
    """Retrieve a registered community retriever by name."""
    return registered_community_retrievers.get(name)
