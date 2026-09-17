"""Search result logging utility."""

from __future__ import annotations

from uuid import UUID

from m_flow.adapters.relational import get_db_adapter

from ..models.Result import Result


async def log_result(query_id: UUID, result: str, user_id: UUID) -> None:
    """Persist a search result to the database."""
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        session.add(Result(value=result, query_id=query_id, user_id=user_id))
        await session.commit()
