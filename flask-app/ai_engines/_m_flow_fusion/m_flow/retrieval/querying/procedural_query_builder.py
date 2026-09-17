"""
Procedural Query Builder.

Simplified: directly use the original user query for retrieval.
No keyword extraction, no multi-level queries, no weight manipulation.
"""

from dataclasses import dataclass
from typing import List, Optional, Any
from m_flow.shared.logging_utils import get_logger

logger = get_logger("ProceduralQueryBuilder")


@dataclass
class QuerySpec:
    """
    Query specification.

    Attributes:
        q: Query string
        kind: Query type (always "query" now)
        weight: Weight (always 1.0, not used for scoring)
    """

    q: str
    kind: str = "query"
    weight: float = 1.0


def build_procedural_queries(
    user_msg: str,
    conversation_ctx: Optional[List[str]] = None,
    trigger_result: Optional[Any] = None,
    max_queries: int = 4,
) -> List[QuerySpec]:
    """
    Build procedural retrieval queries.

    Simplified: returns a single query with the original user message.
    No keyword extraction or multi-level query construction.

    Args:
        user_msg: User message
        conversation_ctx: Conversation context (unused)
        trigger_result: Trigger result (unused, kept for API compatibility)
        max_queries: Maximum number of queries (unused)

    Returns:
        Single QuerySpec with the original query
    """
    # Simply return the original query
    query = QuerySpec(
        q=user_msg.strip()[:500],  # Limit length for vector search
        kind="query",
        weight=1.0,
    )

    logger.debug(f"[query_builder] Using original query: {query.q[:50]}...")

    return [query]
