"""
Abstract base class for retrieval operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type


class BaseRetriever(ABC):
    """
    Interface for retrieval implementations.

    Subclasses must implement context retrieval and completion generation.
    """

    @abstractmethod
    async def get_context(self, query: str) -> Any:
        """
        Retrieve relevant context for the given query.

        Parameters
        ----------
        query
            User query string.

        Returns
        -------
        Context data suitable for completion.
        """
        ...

    @abstractmethod
    async def get_completion(
        self,
        query: str,
        context: Optional[Any] = None,
        session_id: Optional[str] = None,
        response_model: Type[Any] = str,
    ) -> List[Any]:
        """
        Generate completion using query and optional context.

        Parameters
        ----------
        query
            User query string.
        context
            Pre-fetched context or None to fetch automatically.
        session_id
            Optional session identifier for stateful interactions.
        response_model
            Expected response type.

        Returns
        -------
        List of completion results.
        """
        ...
