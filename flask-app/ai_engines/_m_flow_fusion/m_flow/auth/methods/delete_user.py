"""User deletion utility."""

from __future__ import annotations

from fastapi_users.exceptions import UserNotExists

from m_flow.adapters.relational import get_db_adapter
from m_flow.shared.logging_utils import get_logger

from ..get_user_db import get_user_db_context
from ..get_user_manager import get_user_manager_context

_log = get_logger("delete_user")


async def delete_user(email: str) -> None:
    """Delete a user by email address."""
    engine = get_db_adapter()

    try:
        async with engine.get_async_session() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as mgr:
                    user = await mgr.get_by_email(email)
                    await mgr.delete(user)
    except UserNotExists:
        _log.warning("User %s doesn't exist", email)
        raise
