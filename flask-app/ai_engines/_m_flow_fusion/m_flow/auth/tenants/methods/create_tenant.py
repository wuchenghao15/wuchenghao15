"""
Tenant creation.

Creates a new tenant and assigns the user as owner.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from m_flow.adapters.exceptions import ConceptAlreadyExistsError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.methods import get_user
from m_flow.auth.models import Tenant
from m_flow.auth.models.UserTenant import UserTenant


async def create_tenant(
    tenant_name: str,
    user_id: UUID,
    set_as_active_tenant: bool = True,
) -> UUID:
    """
    Provision a new tenant owned by the specified user.

    Args:
        tenant_name: Display name for the tenant.
        user_id: Owner's user ID.
        set_as_active_tenant: Make this the user's active tenant.

    Returns:
        UUID of the created tenant.

    Raises:
        ConceptAlreadyExistsError: If tenant name is taken or user already joined.
    """
    db = get_db_adapter()

    async with db.get_async_session() as sess:
        try:
            usr = await get_user(user_id)

            tenant = Tenant(name=tenant_name, owner_id=user_id)
            sess.add(tenant)
            await sess.flush()

            if set_as_active_tenant:
                usr.tenant_id = tenant.id
                await sess.merge(usr)
                await sess.commit()

            # Link user to tenant
            try:
                stmt = insert(UserTenant).values(user_id=user_id, tenant_id=tenant.id)
                await sess.execute(stmt)
                await sess.commit()
            except IntegrityError:
                raise ConceptAlreadyExistsError(message="User already in tenant")

            return tenant.id

        except IntegrityError as err:
            raise ConceptAlreadyExistsError(message="Tenant name exists") from err
