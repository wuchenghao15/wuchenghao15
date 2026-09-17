"""
Cypher query retrieval.

Executes raw Cypher queries against the graph database.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi.encoders import jsonable_encoder

from m_flow.adapters.graph import get_graph_provider
from m_flow.retrieval.base_retriever import BaseRetriever
from m_flow.retrieval.exceptions import CypherSearchError
from m_flow.shared.logging_utils import get_logger

logger = get_logger("CypherRetriever")


class CypherSearchRetriever(BaseRetriever):
    """
    Executes Cypher queries for graph retrieval.

    Suitable for precise graph traversal when exact
    query structure is known.
    """

    def __init__(
        self,
        user_prompt_path: str = "retrieval_context.txt",
        system_prompt_path: str = "direct_answer.txt",
    ):
        """
        Configure prompt paths.

        Args:
            user_prompt_path: User prompt template.
            system_prompt_path: System prompt template.
        """
        self.user_prompt = user_prompt_path
        self.system_prompt = system_prompt_path

    async def get_context(self, query: str) -> Any:
        """
        Execute Cypher query.

        Args:
            query: Cypher query string.

        Returns:
            Query results as JSON-serializable object.

        Raises:
            CypherSearchError: On query failure.
        """
        try:
            engine = await get_graph_provider()

            if await engine.is_empty():
                logger.warning("Graph is empty, returning no results")
                return []

            raw_result = await engine.query(query)
            return jsonable_encoder(raw_result)

        except Exception as err:
            logger.error("Cypher query failed: %s", str(err))
            raise CypherSearchError() from err

    async def get_completion(
        self,
        query: str,
        context: Optional[Any] = None,
        session_id: Optional[str] = None,
    ) -> Any:
        """
        Get query results.

        Args:
            query: Cypher query string.
            context: Pre-fetched results (optional).
            session_id: Session identifier (unused).

        Returns:
            Query results.
        """
        if context is None:
            context = await self.get_context(query)
        return context
