"""
Dataset permission verification.

Validates user has required permission on dataset.
"""

from __future__ import annotations

from uuid import UUID

from m_flow.auth.methods import get_seed_user
from .get_specific_user_permission_datasets import get_specific_user_permission_datasets
from m_flow.shared.logging_utils import get_logger

from ...models import User

logger = get_logger()


async def check_permission_on_dataset(
    user: User,
    permission_type: str,
    dataset_id: UUID,
) -> None:
    """
    Verify permission on dataset.

    Uses default user if none provided.
    Raises if permission denied.

    Args:
        user: Requesting user (or None).
        permission_type: Required permission name.
        dataset_id: Target dataset.

    Raises:
        PermissionError: If access denied.
    """
    if user is None:
        user = await get_seed_user()

    await get_specific_user_permission_datasets(
        user.id,
        permission_type,
        [dataset_id],
    )
