"""
Grant dataset permissions to principals.

Manages ACL entries for dataset-level access control.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import PermissionNotFoundError
from m_flow.auth.permissions import PERMISSION_TYPES
from ...models import ACL, Principal

from ._get_or_create_permission import get_or_create_permission


class GivePermissionOnDatasetError(Exception):
    """Raised when permission grant fails."""

    message: str = "Failed to give permission on dataset"


@retry(
    retry=retry_if_exception_type(GivePermissionOnDatasetError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=6),
)
async def give_permission_on_dataset(
    principal: Principal,
    dataset_id: UUID,
    permission_name: str,
) -> None:
    """
    Grant permission on dataset to principal.

    Creates ACL entry linking principal, dataset, and permission.
    Idempotent - skips if entry already exists.

    Args:
        principal: User or group receiving permission.
        dataset_id: Target dataset UUID.
        permission_name: Permission type (e.g., "read", "write").

    Raises:
        PermissionNotFoundError: Invalid permission name.
        GivePermissionOnDatasetError: Database conflict.
    """
    if permission_name not in PERMISSION_TYPES:
        raise PermissionNotFoundError(message=f"Permission '{permission_name}' not in allowed types")

    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Get or create permission (concurrency-safe using SAVEPOINT)
        perm = await get_or_create_permission(session, permission_name)

        # Check for existing ACL entry
        existing = await session.execute(
            select(ACL).where(
                ACL.principal_id == principal.id,
                ACL.dataset_id == dataset_id,
                ACL.permission_id == perm.id,
            )
        )

        if existing.scalars().first() is not None:
            return  # Already granted

        # Create new ACL entry with SAVEPOINT for safety
        try:
            async with session.begin_nested():
                acl = ACL(
                    principal_id=principal.id,
                    dataset_id=dataset_id,
                    permission=perm,
                )
                session.add(acl)
            await session.commit()
        except IntegrityError:
            # ACL already exists (concurrent creation) - this is fine
            pass
