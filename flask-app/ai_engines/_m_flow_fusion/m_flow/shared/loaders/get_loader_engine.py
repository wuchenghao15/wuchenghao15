"""
Global loader engine accessor.

Provides a cached singleton pattern for accessing the shared
LoaderEngine instance throughout the M-flow application.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .LoaderEngine import LoaderEngine


@lru_cache(maxsize=1)
def get_loader_engine() -> "LoaderEngine":
    """
    Retrieve the application-wide loader engine singleton.

    Uses LRU caching to ensure only one engine instance exists.
    The engine is lazily created on first access with all
    registered file loaders.

    Returns:
        The shared LoaderEngine instance.

    Example:
        >>> engine = get_loader_engine()
        >>> result = await engine.load_file("/path/to/doc.pdf")
    """
    from .create_loader_engine import create_loader_engine

    return create_loader_engine()


def reset_loader_engine() -> None:
    """
    Clear the cached loader engine instance.

    Useful for testing or when loader configuration changes.
    The next call to get_loader_engine() will create a fresh instance.
    """
    get_loader_engine.cache_clear()
