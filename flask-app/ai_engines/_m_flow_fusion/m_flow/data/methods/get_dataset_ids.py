"""
Dataset ID resolution for write operations.

Transforms dataset names to UUIDs with ownership validation.
"""

from __future__ import annotations

from typing import Union
from uuid import UUID

from m_flow.data.exceptions import DatasetTypeError
from m_flow.data.methods import get_datasets


async def get_dataset_ids(
    datasets: Union[list[str], list[UUID]],
    user,
) -> list[UUID]:
    """
    Resolve dataset identifiers for write access.

    UUID inputs are returned directly.
    String inputs are matched against user-owned datasets.

    Args:
        datasets: List of dataset names or UUIDs.
        user: User requesting write access.

    Returns:
        List of validated dataset UUIDs.

    Raises:
        DatasetTypeError: Mixed or unsupported input types.
    """
    # Direct UUID passthrough
    if all(isinstance(d, UUID) for d in datasets):
        return list(datasets)

    # Name-to-UUID resolution
    if all(isinstance(d, str) for d in datasets):
        return await _resolve_names(datasets, user)

    raise DatasetTypeError(f"Unsupported dataset types: {datasets}")


async def _resolve_names(names: list[str], user) -> list[UUID]:
    """Resolve dataset names to UUIDs for user."""
    user_datasets = await get_datasets(user.id)

    # Filter by name match and tenant
    matched = [ds.id for ds in user_datasets if ds.name in names and ds.tenant_id == user.tenant_id]

    return matched
