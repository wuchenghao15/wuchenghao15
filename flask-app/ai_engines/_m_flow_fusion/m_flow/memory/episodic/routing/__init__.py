"""Routing module for episodic memory."""

from .document_router import route_documents_to_episodes, _MIN_CONCURRENCY_FOR_PARALLEL

__all__ = ["route_documents_to_episodes", "_MIN_CONCURRENCY_FOR_PARALLEL"]
