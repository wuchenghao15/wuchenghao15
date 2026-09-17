"""
Authorized permission granting.

Grants dataset permissions with owner validation.
"""

from __future__ import annotations

from typing import List, Union
from uuid import UUID

from .get_principal import get_principal
from .get_specific_user_permission_datasets import get_specific_user_permission_datasets
from .give_permission_on_dataset import give_permission_on_dataset


async def authorized_give_permission_on_datasets(
    principal_id: UUID,
    dataset_ids: Union[List[UUID], UUID],
    permission_name: str,
    owner_id: UUID,
) -> None:
    """
    Grant permissions with authorization check.

    Verifies owner has share permission before granting.

    Args:
        principal_id: Recipient user.
        dataset_ids: Target datasets (single or list).
        permission_name: Permission to grant.
        owner_id: Requesting user (must have share permission).

    Raises:
        PermissionDeniedError: Owner lacks share permission.
    """
    # Normalize to list
    ids = [dataset_ids] if not isinstance(dataset_ids, list) else dataset_ids

    # Get recipient
    principal = await get_principal(principal_id)

    # Verify owner can share
    datasets = await get_specific_user_permission_datasets(owner_id, "share", ids)

    # Grant permissions
    for ds in datasets:
        await give_permission_on_dataset(principal, ds.id, permission_name)
