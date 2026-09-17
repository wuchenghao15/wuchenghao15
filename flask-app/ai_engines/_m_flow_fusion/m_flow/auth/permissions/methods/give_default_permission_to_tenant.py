"""Assigns default permissions to tenants."""

from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from m_flow.adapters.exceptions import ConceptAlreadyExistsError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import TenantNotFoundError
from m_flow.auth.models import Tenant, TenantDefaultPermissions

from ._get_or_create_permission import get_or_create_permission


async def give_default_permission_to_tenant(tenant_id: UUID, permission_name: str) -> None:
    """Grant a default permission to a specific tenant.

    Args:
        tenant_id: UUID of the target tenant.
        permission_name: Name of the permission to grant.

    Raises:
        TenantNotFoundError: If no tenant matches the given id.
        ConceptAlreadyExistsError: If permission is already assigned.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Fetch tenant
        tenant_query = select(Tenant).where(Tenant.id == tenant_id)
        tenant = (await session.execute(tenant_query)).scalars().first()

        if not tenant:
            raise TenantNotFoundError

        # Get or create permission (concurrency-safe)
        perm = await get_or_create_permission(session, permission_name)

        # Assign permission to tenant
        try:
            await session.execute(insert(TenantDefaultPermissions).values(tenant_id=tenant.id, permission_id=perm.id))
        except IntegrityError:
            raise ConceptAlreadyExistsError(message="Tenant permission already exists.")

        await session.commit()
