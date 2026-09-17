"""
Abstract base class for graph-based retrieval operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type

from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge


class BaseGraphRetriever(ABC):
    """
    Interface for graph-based retrieval implementations.

    Operates on graph edges (triplets) as context.
    """

    @abstractmethod
    async def get_context(self, query: str) -> List[Edge]:
        """
        Retrieve relevant graph edges for the given query.

        Parameters
        ----------
        query
            User query string.

        Returns
        -------
        List of matching edges (triplets).
        """
        ...

    @abstractmethod
    async def get_completion(
        self,
        query: str,
        context: Optional[List[Edge]] = None,
        session_id: Optional[str] = None,
        response_model: Type[Any] = str,
    ) -> List[Any]:
        """
        Generate completion using query and graph context.

        Parameters
        ----------
        query
            User query string.
        context
            Pre-fetched edges or None to fetch automatically.
        session_id
            Optional session identifier.
        response_model
            Expected response type.

        Returns
        -------
        List of completion results.
        """
        ...
