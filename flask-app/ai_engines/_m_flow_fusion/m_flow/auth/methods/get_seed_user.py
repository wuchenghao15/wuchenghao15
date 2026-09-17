"""
Default user retrieval.

Fetches or creates the default system user.
"""

from __future__ import annotations

from sqlalchemy.exc import NoResultFound
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from m_flow.adapters.exceptions import DatabaseNotCreatedError
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.exceptions.exceptions import UserNotFoundError
from m_flow.auth.methods.create_default_user import create_default_user
from m_flow.auth.models import User
from m_flow.base_config import get_base_config


async def get_seed_user() -> User:
    """
    Retrieve or create default system user.

    Looks up user by configured email. Creates new default
    user if not found.

    Returns:
        Default User instance.

    Raises:
        DatabaseNotCreatedError: Database not initialized.
        UserNotFoundError: User lookup failed.
    """
    engine = get_db_adapter()
    cfg = get_base_config()
    email = cfg.default_user_email or "default_user@example.com"

    try:
        async with engine.get_async_session() as session:
            stmt = (
                select(User)
                .options(
                    selectinload(User.roles),
                    selectinload(User.tenants),
                )
                .where(User.email == email)
            )

            result = await session.execute(stmt)
            user = result.scalars().first()

            if user is None:
                return await create_default_user()

            return user

    except Exception as e:
        if "principals" in str(e.args):
            raise DatabaseNotCreatedError() from e
        if isinstance(e, NoResultFound):
            raise UserNotFoundError(f"Default user not found: {email}") from e
        raise
