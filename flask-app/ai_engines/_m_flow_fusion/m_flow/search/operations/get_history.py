"""
Query history retrieval.

Fetches interleaved user queries and system results for a user.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import literal, select

from m_flow.adapters.relational import get_db_adapter
from ..models.Query import Query
from ..models.Result import Result


async def get_history(user_id: UUID, limit: int = 10) -> list:
    """
    Retrieve conversation history for a user.

    Combines Query and Result records, ordered chronologically.

    Args:
        user_id: Target user identifier.
        limit: Maximum records to return (0 = unlimited).

    Returns:
        List of (id, text, created_at, user_type) tuples.
    """
    engine = get_db_adapter()

    # User queries
    user_msgs = select(
        Query.id,
        Query.text.label("text"),
        Query.created_at,
        literal("user").label("user"),
    ).where(Query.user_id == user_id)

    # System responses
    sys_msgs = select(
        Result.id,
        Result.value.label("text"),
        Result.created_at,
        literal("system").label("user"),
    ).where(Result.user_id == user_id)

    # Combine and sort
    combined = user_msgs.union(sys_msgs).order_by("created_at")

    if limit > 0:
        combined = combined.limit(limit)

    async with engine.get_async_session() as session:
        rows = await session.execute(combined)
        return list(rows.all())
