"""Assigns default permissions to roles."""

from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from m_flow.adapters.exceptions import ConceptAlreadyExistsError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import RoleNotFoundError
from m_flow.auth.models import Role, RoleDefaultPermissions

from ._get_or_create_permission import get_or_create_permission


async def give_default_permission_to_role(role_id: UUID, permission_name: str) -> None:
    """Grant a default permission to a specific role.

    Args:
        role_id: UUID of the target role.
        permission_name: Name of the permission to grant.

    Raises:
        RoleNotFoundError: If no role matches the given id.
        ConceptAlreadyExistsError: If permission is already assigned.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Fetch role
        role_query = select(Role).where(Role.id == role_id)
        role = (await session.execute(role_query)).scalars().first()

        if not role:
            raise RoleNotFoundError

        # Get or create permission (concurrency-safe)
        perm = await get_or_create_permission(session, permission_name)

        # Assign permission to role
        try:
            await session.execute(insert(RoleDefaultPermissions).values(role_id=role.id, permission_id=perm.id))
        except IntegrityError:
            raise ConceptAlreadyExistsError(message="Role permission already exists.")

        await session.commit()
