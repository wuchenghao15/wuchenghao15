"""
Prompts API Routers.

Provides REST endpoints for managing LLM prompt templates.
"""

from .get_prompts_router import get_prompts_router

__all__ = ["get_prompts_router"]
