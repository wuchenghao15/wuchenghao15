"""
Dataset permission filtering.

Filters datasets by user permission with validation.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from m_flow.auth.exceptions import PermissionDeniedError
from m_flow.auth.methods import get_user
from m_flow.auth.permissions.methods.get_all_user_permission_datasets import (
    get_all_user_permission_datasets,
)
from m_flow.data.models.Dataset import Dataset


async def get_specific_user_permission_datasets(
    user_id: UUID,
    permission_type: str,
    dataset_ids: Optional[list[UUID]] = None,
) -> list[Dataset]:
    """
    Get datasets user has permission for.

    Optionally filters to specific dataset IDs and validates
    user has access to all requested datasets.

    Args:
        user_id: Target user.
        permission_type: Required permission name.
        dataset_ids: Optional filter list.

    Returns:
        Accessible datasets.

    Raises:
        PermissionDeniedError: Missing access to requested datasets.
    """
    user = await get_user(user_id)

    # Get all permitted datasets
    permitted = await get_all_user_permission_datasets(user, permission_type)

    # Filter to requested if specified
    if dataset_ids:
        filtered = [ds for ds in permitted if ds.id in dataset_ids]

        # Verify complete access
        if len(filtered) != len(dataset_ids):
            raise PermissionDeniedError(f"Missing {permission_type} permission for some requested datasets")

        return filtered

    # Return all permitted
    if not permitted:
        raise PermissionDeniedError(f"No datasets with {permission_type} permission")

    return permitted
