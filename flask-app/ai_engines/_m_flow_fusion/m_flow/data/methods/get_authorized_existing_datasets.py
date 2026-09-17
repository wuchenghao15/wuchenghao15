"""
Fetch authorized existing datasets.

Filters datasets based on user permissions.
"""

from __future__ import annotations

from typing import Union
from uuid import UUID

from m_flow.auth.models import User
from m_flow.auth.permissions.methods import (
    get_all_user_permission_datasets,
    get_specific_user_permission_datasets,
)
from m_flow.data.methods.get_dataset_ids import get_dataset_ids
from m_flow.data.models import Dataset


async def get_authorized_existing_datasets(
    datasets: Union[list[str], list[UUID]],
    permission_type: str,
    user: User,
) -> list[Dataset]:
    """
    Retrieve existing datasets the user has access to.

    Args:
        datasets: Names or UUIDs to filter.
        permission_type: Required permission (e.g., 'write', 'read').
        user: Requesting user.

    Returns:
        List of authorized Dataset objects.
    """
    if not datasets:
        return await get_all_user_permission_datasets(user, permission_type)

    ds_ids = await get_dataset_ids(datasets, user)
    if not ds_ids:
        return []

    return await get_specific_user_permission_datasets(user.id, permission_type, ds_ids)
