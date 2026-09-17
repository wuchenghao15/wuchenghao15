"""
Graph API module.

Provides REST API endpoints for knowledge graph visualization.
"""

from .routers.get_graph_router import get_graph_router

__all__ = ["get_graph_router"]
