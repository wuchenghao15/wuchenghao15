"""
Role Creation Module
====================

Provides functionality for creating new roles within a tenant's
permission system. Roles can be assigned to users to grant
specific capabilities.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from m_flow.adapters.exceptions import ConceptAlreadyExistsError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.methods import get_user
from m_flow.auth.permissions.methods import get_tenant
from m_flow.auth.exceptions import PermissionDeniedError
from m_flow.auth.models import Role


async def create_role(role_name: str, owner_id: UUID) -> UUID:
    """
    Create a new role within the owner's tenant.

    This function verifies that the requesting user has ownership
    of the tenant before allowing role creation.

    Parameters
    ----------
    role_name : str
        Display name for the new role.
    owner_id : UUID
        Identifier of the user making the request.

    Returns
    -------
    UUID
        The unique identifier of the newly created role.

    Raises
    ------
    PermissionDeniedError
        If the requesting user is not the tenant owner.
    ConceptAlreadyExistsError
        If a role with the same name already exists in the tenant.

    Example
    -------
    >>> role_id = await create_role("Editor", user.id)
    """
    db = get_db_adapter()

    async with db.get_async_session() as session:
        # Verify requester identity and tenant ownership
        requester = await get_user(owner_id)
        tenant_record = await get_tenant(requester.tenant_id)

        # Only tenant owner can create roles
        if owner_id != tenant_record.owner_id:
            raise PermissionDeniedError("Only the tenant owner can create new roles.")

        try:
            # Initialize new role entity
            new_role = Role(
                name=role_name,
                tenant_id=tenant_record.id,
            )
            session.add(new_role)

        except IntegrityError as integrity_err:
            raise ConceptAlreadyExistsError(
                message="A role with this name already exists in the tenant."
            ) from integrity_err

        # Persist and return the new role ID
        await session.commit()
        await session.refresh(new_role)

        return new_role.id
