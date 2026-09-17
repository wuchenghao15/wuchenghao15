"""
Factory for obtaining the configured vector database engine.
"""

from __future__ import annotations

from .config import get_vectordb_context_config
from .create_vector_engine import create_vector_engine


def get_vector_provider():
    """
    Instantiate and return the vector DB engine based on runtime config.

    The configuration is context-aware (e.g., respects async context vars).
    """
    cfg = get_vectordb_context_config()
    return create_vector_engine(**cfg)
