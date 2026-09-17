"""
Tenant membership management.

Adds users to tenants with ownership verification.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from m_flow.adapters.exceptions import ConceptAlreadyExistsError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import (
    PermissionDeniedError,
    TenantNotFoundError,
    UserNotFoundError,
)
from m_flow.auth.methods import get_user
from m_flow.auth.models.UserTenant import UserTenant
from m_flow.auth.permissions.methods import get_tenant


async def add_user_to_tenant(
    user_id: UUID,
    tenant_id: UUID,
    owner_id: UUID,
    set_as_active_tenant: Optional[bool] = False,
) -> None:
    """
    Add user to tenant organization.

    Only tenant owner can add members.

    Args:
        user_id: User to add.
        tenant_id: Target tenant.
        owner_id: Requesting user (must own tenant).
        set_as_active_tenant: Activate tenant for user.

    Raises:
        UserNotFoundError: User not found.
        TenantNotFoundError: Tenant not found.
        PermissionDeniedError: Requester not owner.
        ConceptAlreadyExistsError: User already member.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as sess:
        user = await get_user(user_id)
        tenant = await get_tenant(tenant_id)

        if not user:
            raise UserNotFoundError()
        if not tenant:
            raise TenantNotFoundError()

        # Verify ownership
        if tenant.owner_id != owner_id:
            raise PermissionDeniedError(message="Only tenant owner can add members")

        # Set active if requested
        if set_as_active_tenant:
            user.tenant_id = tenant_id
            await sess.merge(user)
            await sess.commit()

        # Create membership
        try:
            stmt = insert(UserTenant).values(
                user_id=user_id,
                tenant_id=tenant_id,
            )
            await sess.execute(stmt)
            await sess.commit()
        except IntegrityError:
            raise ConceptAlreadyExistsError(message="User already in tenant")
