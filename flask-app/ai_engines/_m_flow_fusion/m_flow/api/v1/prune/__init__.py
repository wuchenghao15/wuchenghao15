"""
Prune API Package.

Provides administrative data cleanup operations for M-flow.

Exports:
    prune: Static class with cleanup methods (all, prune_data, prune_system)
    get_prune_router: FastAPI router factory for REST API endpoints

Warning:
    These operations are destructive and irreversible.
    Use with caution in production environments.
"""

from __future__ import annotations

from .prune import prune as prune

# Router export (may not be available in minimal installations)
try:
    from .routers import get_prune_router
except ImportError:
    get_prune_router = None  # type: ignore[assignment, misc]

__all__ = ["prune", "get_prune_router"]
