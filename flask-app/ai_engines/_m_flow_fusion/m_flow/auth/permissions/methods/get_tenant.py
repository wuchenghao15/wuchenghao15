"""Retrieves tenant information by identifier."""

from uuid import UUID

import sqlalchemy.exc
from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import TenantNotFoundError
from ...models.Tenant import Tenant


async def get_tenant(tenant_id: UUID) -> Tenant:
    """Fetch tenant entity by its unique identifier.

    Args:
        tenant_id: UUID of the tenant to retrieve.

    Returns:
        Tenant entity matching the given id.

    Raises:
        TenantNotFoundError: If no tenant matches the provided id.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        try:
            query = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(query)
            tenant = result.unique().scalar_one()

            if tenant is None:
                raise TenantNotFoundError

            return tenant
        except sqlalchemy.exc.NoResultFound:
            raise TenantNotFoundError(message=f"Tenant not found: {tenant_id}")
