"""
Role membership management.

Adds users to roles with permission validation.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from m_flow.adapters.exceptions import ConceptAlreadyExistsError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import (
    PermissionDeniedError,
    RoleNotFoundError,
    TenantNotFoundError,
    UserNotFoundError,
)
from m_flow.auth.models import Role, Tenant, User, UserRole


async def add_user_to_role(
    user_id: UUID,
    role_id: UUID,
    owner_id: UUID,
) -> None:
    """
    Assign user to role with ownership validation.

    Args:
        user_id: Target user.
        role_id: Target role.
        owner_id: Requesting user (must own tenant).

    Raises:
        UserNotFoundError: User not found.
        RoleNotFoundError: Role not found.
        TenantNotFoundError: User not in role's tenant.
        PermissionDeniedError: Requester not tenant owner.
        ConceptAlreadyExistsError: User already in role.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Fetch entities
        user = (await session.execute(select(User).where(User.id == user_id))).scalars().first()

        role = (await session.execute(select(Role).where(Role.id == role_id))).scalars().first()

        # Validate existence
        if not user:
            raise UserNotFoundError()
        if not role:
            raise RoleNotFoundError()

        # Check tenant membership
        tenant = (await session.execute(select(Tenant).where(Tenant.id == role.tenant_id))).scalars().first()

        user_tenants = await user.awaitable_attrs.tenants
        user_tenant_ids = {t.id for t in user_tenants}

        if role.tenant_id not in user_tenant_ids:
            raise TenantNotFoundError(message="User not in role's tenant")

        # Verify ownership
        if tenant.owner_id != owner_id:
            raise PermissionDeniedError(message="Not authorized to manage this role")

        # Create association
        try:
            stmt = insert(UserRole).values(user_id=user_id, role_id=role_id)
            await session.execute(stmt)
            await session.commit()
        except IntegrityError:
            raise ConceptAlreadyExistsError(message="User already in role")
