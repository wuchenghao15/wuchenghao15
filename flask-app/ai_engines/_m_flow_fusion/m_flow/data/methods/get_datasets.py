"""Dataset retrieval utility."""

from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter

from ..models import Dataset


async def get_datasets(user_id: UUID) -> List[Dataset]:
    """Return all datasets owned by the specified user."""
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        result = await session.scalars(select(Dataset).filter(Dataset.owner_id == user_id))
        return list(result.all())
