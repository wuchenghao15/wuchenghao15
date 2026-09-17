"""
Dataset retrieval by name.

Fetches datasets owned by a user matching given names.
"""

from __future__ import annotations

from typing import Union
from uuid import UUID

from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from ..models import Dataset


async def get_datasets_by_name(
    dataset_names: Union[str, list[str]],
    user_id: UUID,
) -> list[Dataset]:
    """
    Retrieve datasets by name for a specific user.

    Args:
        dataset_names: Single name or list of names.
        user_id: Owner user UUID.

    Returns:
        List of matching Dataset records.
    """
    engine = get_db_adapter()

    # Normalize to list
    names = [dataset_names] if isinstance(dataset_names, str) else dataset_names

    async with engine.get_async_session() as session:
        query = select(Dataset).where(Dataset.owner_id == user_id).where(Dataset.name.in_(names))
        result = await session.scalars(query)
        return list(result.all())
