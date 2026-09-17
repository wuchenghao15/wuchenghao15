"""Assigns default permissions to users."""

from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from m_flow.adapters.exceptions import ConceptAlreadyExistsError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions import UserNotFoundError
from m_flow.auth.models import User, UserDefaultPermissions

from ._get_or_create_permission import get_or_create_permission


async def give_default_permission_to_user(user_id: UUID, permission_name: str) -> None:
    """Grant a default permission to a specific user.

    Args:
        user_id: UUID of the target user.
        permission_name: Name of the permission to grant.

    Raises:
        UserNotFoundError: If no user matches the given id.
        ConceptAlreadyExistsError: If permission is already assigned.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        # Fetch user
        user_query = select(User).where(User.id == user_id)
        user = (await session.execute(user_query)).scalars().first()

        if not user:
            raise UserNotFoundError

        # Get or create permission (concurrency-safe)
        perm = await get_or_create_permission(session, permission_name)

        # Assign permission to user
        try:
            await session.execute(insert(UserDefaultPermissions).values(user_id=user.id, permission_id=perm.id))
        except IntegrityError:
            raise ConceptAlreadyExistsError(message="User permission already exists.")

        await session.commit()
