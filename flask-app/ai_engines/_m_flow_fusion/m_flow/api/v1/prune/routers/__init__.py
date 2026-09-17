"""
Prune API Routers Package.

Exports the prune router factory for FastAPI integration.
"""

from __future__ import annotations

from .get_prune_router import get_prune_router

__all__ = ["get_prune_router"]
