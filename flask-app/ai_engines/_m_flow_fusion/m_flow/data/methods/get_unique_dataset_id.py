"""
Dataset ID generation with legacy compatibility.

Generates deterministic UUIDs for datasets while maintaining
backward compatibility with pre-tenant datasets.
"""

from __future__ import annotations

from typing import Union
from uuid import NAMESPACE_OID, UUID, uuid5

from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.models import User
from m_flow.data.models.Dataset import Dataset


async def get_unique_dataset_id(
    dataset_name: Union[str, UUID],
    user: User,
) -> UUID:
    """
    Generate or retrieve unique dataset identifier.

    Supports both modern (user + tenant) and legacy (user only) ID schemes.
    Checks database for existing legacy dataset to maintain compatibility.

    Args:
        dataset_name: Dataset name or existing UUID.
        user: Owner user.

    Returns:
        Deterministic UUID for the dataset.
    """
    if isinstance(dataset_name, UUID):
        return dataset_name

    legacy_id = _compute_legacy_id(dataset_name, user)
    modern_id = _compute_modern_id(dataset_name, user)

    # Check if dataset exists
    engine = get_db_adapter()
    async with engine.get_async_session() as session:
        existing = await session.execute(select(Dataset).where(Dataset.id == legacy_id))

        if existing.scalar_one_or_none() is not None:
            return legacy_id

    return modern_id


def _compute_legacy_id(name: str, user: User) -> UUID:
    """Generate legacy ID (pre-tenant support)."""
    seed = f"{name}{user.id}"
    return uuid5(NAMESPACE_OID, seed)


def _compute_modern_id(name: str, user: User) -> UUID:
    """Generate modern ID with tenant isolation."""
    seed = f"{name}{user.id}{user.tenant_id}"
    return uuid5(NAMESPACE_OID, seed)
