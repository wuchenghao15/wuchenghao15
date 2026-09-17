"""
Tenant selection.

Switches user's active tenant context.
"""

from __future__ import annotations

from typing import Union
from uuid import UUID

import sqlalchemy.exc
from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import TenantNotFoundError, UserNotFoundError
from m_flow.auth.methods.get_user import get_user
from m_flow.auth.models.User import User
from m_flow.auth.models.UserTenant import UserTenant
from m_flow.auth.permissions.methods import get_tenant


async def select_tenant(
    user_id: UUID,
    tenant_id: Union[UUID, None],
) -> User:
    """
    Set user's active tenant.

    Pass None to reset to single-user mode.

    Args:
        user_id: Target user.
        tenant_id: Tenant to activate (or None).

    Returns:
        Updated User instance.

    Raises:
        UserNotFoundError: User not found.
        TenantNotFoundError: Tenant not found or user not member.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as sess:
        user = await get_user(user_id)

        if not user:
            raise UserNotFoundError()

        # Clear tenant if None
        if tenant_id is None:
            user.tenant_id = None
            await sess.merge(user)
            await sess.commit()
            return user

        # Validate tenant exists
        tenant = await get_tenant(tenant_id)
        if not tenant:
            raise TenantNotFoundError()

        # Verify membership
        membership_query = (
            select(UserTenant).where(UserTenant.user_id == user.id).where(UserTenant.tenant_id == tenant_id)
        )

        try:
            result = await sess.execute(membership_query)
            result.scalar_one()
        except sqlalchemy.exc.NoResultFound:
            raise TenantNotFoundError("User not in tenant")

        # Update active tenant
        user.tenant_id = tenant_id
        await sess.merge(user)
        await sess.commit()

        return user
