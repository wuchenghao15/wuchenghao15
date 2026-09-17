"""Query logging operations."""

from __future__ import annotations

from uuid import UUID

from m_flow.adapters.relational import get_db_adapter

from ..models.Query import Query


async def log_query(query_text: str, query_type: str, user_id: UUID) -> Query:
    """Persist a search query to the database."""
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        q = Query(text=query_text, query_type=query_type, user_id=user_id)
        session.add(q)
        await session.commit()
        return q
