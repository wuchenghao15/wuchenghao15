"""User lookup by email."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from m_flow.adapters.relational import get_db_adapter

from ..models import User


async def get_user_by_email(user_email: str) -> Optional[User]:
    """
    Retrieve a user by email with roles and tenants loaded.

    Returns None if user not found.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        query = select(User).options(joinedload(User.roles), joinedload(User.tenants)).where(User.email == user_email)
        result = await session.execute(query)
        return result.scalar()
