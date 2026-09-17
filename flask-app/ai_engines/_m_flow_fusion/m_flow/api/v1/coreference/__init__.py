"""
Coreference Resolution API endpoints.

Provides configuration and statistics endpoints for the
coreference preprocessing module.
"""

from .routers import get_coreference_router

__all__ = ["get_coreference_router"]
