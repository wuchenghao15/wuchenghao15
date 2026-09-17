"""
Deletion count preview.

Calculates items to be deleted before actual deletion.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.sql import func

from m_flow.adapters.exceptions.exceptions import ConceptNotFoundError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.methods import get_user
from m_flow.auth.models import User
from m_flow.cli.exceptions import CliCommandException
from m_flow.data.models import Data, Dataset, DatasetEntry


@dataclass
class DeletionCountsPreview:
    """Summary of items to be deleted."""

    datasets: int = 0
    data_entries: int = 0
    users: int = 0


async def get_deletion_counts(
    dataset_name: str = None,
    user_id: str = None,
    all_data: bool = False,
) -> DeletionCountsPreview:
    """
    Calculate deletion impact.

    Args:
        dataset_name: Delete specific dataset.
        user_id: Delete user's data.
        all_data: Delete everything.

    Returns:
        Preview of deletion counts.
    """
    counts = DeletionCountsPreview()
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        if dataset_name:
            return await _count_dataset_deletion(session, dataset_name, counts)

        if all_data:
            return await _count_all_deletion(session, counts)

        if user_id:
            return await _count_user_deletion(session, user_id, counts)

    return counts


async def _count_dataset_deletion(session, name: str, counts) -> DeletionCountsPreview:
    """Count items in named dataset."""
    result = await session.execute(select(Dataset).where(Dataset.name == name))
    ds = result.scalar_one_or_none()

    if ds is None:
        raise CliCommandException(f"Dataset not found: {name}", error_code=1)

    entry_count = (
        await session.execute(select(func.count()).select_from(DatasetEntry).where(DatasetEntry.dataset_id == ds.id))
    ).scalar_one()

    counts.users = 1
    counts.datasets = 1
    counts.data_entries = entry_count
    return counts


async def _count_all_deletion(session, counts) -> DeletionCountsPreview:
    """Count all items in system."""
    counts.datasets = (await session.execute(select(func.count()).select_from(Dataset))).scalar_one()

    counts.data_entries = (await session.execute(select(func.count()).select_from(Data))).scalar_one()

    counts.users = (await session.execute(select(func.count()).select_from(User))).scalar_one()

    return counts


async def _count_user_deletion(session, user_id_str: str, counts) -> DeletionCountsPreview:
    """Count items owned by user."""
    try:
        uid = UUID(user_id_str)
        user = await get_user(uid)
    except (ValueError, ConceptNotFoundError):
        raise CliCommandException(f"User not found: {user_id_str}", error_code=1)

    counts.users = 1

    datasets = (await session.execute(select(Dataset).where(Dataset.owner_id == user.id))).scalars().all()

    counts.datasets = len(datasets)

    if datasets:
        ds_ids = [d.id for d in datasets]
        counts.data_entries = (
            await session.execute(
                select(func.count()).select_from(DatasetEntry).where(DatasetEntry.dataset_id.in_(ds_ids))
            )
        ).scalar_one()
    else:
        counts.data_entries = 0

    return counts
