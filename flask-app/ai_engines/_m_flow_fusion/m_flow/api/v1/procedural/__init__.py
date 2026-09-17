# m_flow/api/v1/procedural/__init__.py
"""
Procedural Memory API endpoints.
"""

from .routers.extract_from_episodic_router import get_extract_from_episodic_router

__all__ = [
    "get_extract_from_episodic_router",
]
