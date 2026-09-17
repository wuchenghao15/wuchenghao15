"""
Principal Dataset Access
========================

Retrieves datasets that a principal has specific permissions for.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.models.Dataset import Dataset

from ...models.Principal import Principal
from ...models.ACL import ACL


async def get_principal_datasets(
    principal: Principal,
    permission_type: str,
) -> list[Dataset]:
    """
    Retrieve datasets accessible to a principal with a given permission.

    Queries the ACL table to find all datasets where the principal
    has been granted the specified permission type.

    Parameters
    ----------
    principal : Principal
        The user or service account to check permissions for.
    permission_type : str
        The permission name to filter by (e.g., 'read', 'write').

    Returns
    -------
    list[Dataset]
        Datasets the principal can access with the specified permission.
    """
    db = get_db_adapter()

    async with db.get_async_session() as session:
        # Build query for ACL entries matching principal and permission
        stmt = (
            select(ACL)
            .join(ACL.permission)
            .options(joinedload(ACL.dataset))
            .where(ACL.principal_id == principal.id)
            .where(ACL.permission.has(name=permission_type))
        )

        result = await session.execute(stmt)
        acl_records = result.unique().scalars().all()

        # Extract datasets from ACL entries
        return [acl.dataset for acl in acl_records]
