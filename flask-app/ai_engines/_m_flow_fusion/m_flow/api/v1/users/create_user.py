"""
User creation API helper module.
"""

from __future__ import annotations

from m_flow.auth.methods import create_user as _create_user_impl
from m_flow.auth.models import User


async def create_user(
    email: str,
    password: str,
    is_superuser: bool = False,
) -> User:
    """
    Create a verified user.

    Args:
        email: User email.
        password: User password.
        is_superuser: Whether the user is a superuser.

    Returns:
        Created User object.
    """
    new_user = await _create_user_impl(
        email=email,
        password=password,
        is_superuser=is_superuser,
        is_verified=True,
    )
    return new_user
