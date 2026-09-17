"""
User retrieval by ID.

Fetches a user with associated roles and tenants.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from m_flow.adapters.exceptions import ConceptNotFoundError
from m_flow.adapters.relational import get_db_adapter

from ..models import User


async def get_user(user_id: UUID) -> User:
    """
    Retrieve a user by primary key.

    Eagerly loads roles and tenants relationships.

    Args:
        user_id: UUID of the user.

    Returns:
        User model instance.

    Raises:
        ConceptNotFoundError: If no user exists with the given ID.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as sess:
        stmt = select(User).options(selectinload(User.roles), selectinload(User.tenants)).where(User.id == user_id)
        result = await sess.execute(stmt)
        user = result.scalar()

    if user is None:
        raise ConceptNotFoundError(message=f"User not found: {user_id}")

    return user
