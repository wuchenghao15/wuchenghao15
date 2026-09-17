"""Retrieves role information by tenant and role name."""

from uuid import UUID

import sqlalchemy.exc
from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import RoleNotFoundError
from ...models.Role import Role


async def get_role(tenant_id: UUID, role_name: str) -> Role:
    """Fetch a role by name within a specific tenant.

    Args:
        tenant_id: UUID of the tenant.
        role_name: Name of the role to retrieve.

    Returns:
        Role entity matching the criteria.

    Raises:
        RoleNotFoundError: If no matching role exists.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        try:
            query = select(Role).where(Role.name == role_name).where(Role.tenant_id == tenant_id)
            result = await session.execute(query)
            role = result.unique().scalar_one()

            if role is None:
                raise RoleNotFoundError(message=f"Role '{role_name}' not found for tenant")

            return role
        except sqlalchemy.exc.NoResultFound:
            raise RoleNotFoundError(message=f"Role '{role_name}' not found for tenant")
