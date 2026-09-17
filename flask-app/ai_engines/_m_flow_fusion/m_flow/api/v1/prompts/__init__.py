"""
Prompts API module.

Provides CRUD operations for LLM prompt templates.
"""

from .routers import get_prompts_router

__all__ = ["get_prompts_router"]
