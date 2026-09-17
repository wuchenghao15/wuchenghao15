"""
User permission dataset aggregation.

Collects all datasets a user has access to via direct, tenant, and role permissions.
"""

from __future__ import annotations

from .get_principal_datasets import get_principal_datasets
from m_flow.data.models.Dataset import Dataset
from m_flow.shared.logging_utils import get_logger
from ...models import User

_log = get_logger()


async def get_all_user_permission_datasets(
    user: User,
    permission_type: str,
) -> list[Dataset]:
    """
    Aggregate datasets user can access.

    Collects permissions from:
      - Direct user grants
      - Tenant membership
      - Role assignments

    Args:
        user: Target user.
        permission_type: Permission to check (e.g., "read").

    Returns:
        Deduplicated list of accessible datasets within user's tenant.
    """
    all_datasets = []

    # Direct user permissions
    all_datasets.extend(await get_principal_datasets(user, permission_type))

    # Tenant-level permissions
    tenants = await user.awaitable_attrs.tenants
    for tenant in tenants:
        all_datasets.extend(await get_principal_datasets(tenant, permission_type))

        # Role-level permissions within tenant
        roles = await user.awaitable_attrs.roles
        for role in roles:
            all_datasets.extend(await get_principal_datasets(role, permission_type))

    # Deduplicate by dataset ID (filter out None values that may result from orphaned ACLs)
    unique = {ds.id: ds for ds in all_datasets if ds is not None}

    # Filter to user's current tenant
    return [ds for ds in unique.values() if ds.tenant_id == user.tenant_id]
