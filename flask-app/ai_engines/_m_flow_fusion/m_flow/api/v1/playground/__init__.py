"""Playground — interactive LLM chat with face recognition and memory."""

from .routers.get_playground_router import get_playground_router

# Import the SQLAlchemy model at module level so it registers with
# Base.metadata BEFORE create_all() runs at startup.
from .face_mapping_model import PlaygroundFaceMapping as _PlaygroundFaceMapping  # noqa: F401

__all__ = ["get_playground_router"]
