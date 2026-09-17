"""
Dataset creation.

Creates new datasets with ownership and tenant isolation.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from m_flow.auth.models import User
from m_flow.data.methods.get_unique_dataset_id import get_unique_dataset_id
from m_flow.data.models import Dataset


async def create_dataset(
    dataset_name: str,
    user: User,
    session: AsyncSession,
) -> Dataset:
    """
    Create or retrieve dataset.

    Checks for existing dataset with same name/owner/tenant.
    Creates new if not found.

    Args:
        dataset_name: Dataset identifier.
        user: Owning user.
        session: Active database session.

    Returns:
        Dataset instance.
    """
    # Look for existing
    query = (
        select(Dataset)
        .options(joinedload(Dataset.data))
        .where(Dataset.name == dataset_name)
        .where(Dataset.owner_id == user.id)
        .where(Dataset.tenant_id == user.tenant_id)
    )

    existing = (await session.scalars(query)).first()

    if existing is not None:
        return existing

    # Create new
    ds_id = await get_unique_dataset_id(dataset_name, user)

    ds = Dataset(
        id=ds_id,
        name=dataset_name,
        data=[],
        owner_id=user.id,
        tenant_id=user.tenant_id,
    )

    session.add(ds)
    await session.commit()

    return ds
