"""
User Creation Module
====================

Provides functionality for creating new user accounts within M-flow.
Handles user registration, validation, and initial setup of user
relationships (tenants and roles).
"""

from __future__ import annotations


from fastapi_users.exceptions import UserAlreadyExists

from m_flow.adapters.relational import get_db_adapter
from m_flow.shared.logging_utils import get_logger
from m_flow.auth.get_user_manager import get_user_manager_context
from m_flow.auth.get_user_db import get_user_db_context
from m_flow.auth.models.User import UserCreate

logger = get_logger(__name__)


async def create_user(
    email: str,
    password: str,
    is_superuser: bool = False,
    is_active: bool = True,
    is_verified: bool = False,
    auto_login: bool = False,
):
    """
    Create a new user account in the M-flow system.

    This function handles the complete user creation workflow including
    validation, persistence, and initial relationship setup.

    Parameters
    ----------
    email : str
        User's email address (must be unique in the system).
    password : str
        Plain text password that will be hashed before storage.
    is_superuser : bool, optional
        Grant superuser privileges if True. Defaults to False.
    is_active : bool, optional
        Account active status. Inactive users cannot authenticate.
        Defaults to True.
    is_verified : bool, optional
        Email verification status. Defaults to False.
    auto_login : bool, optional
        If True, refreshes the user object for immediate session use.
        Defaults to False.

    Returns
    -------
    User
        The newly created user object with populated relationships.

    Raises
    ------
    UserAlreadyExists
        When an account with the given email already exists.

    Example
    -------
    >>> new_user = await create_user(
    ...     email="user@example.com",
    ...     password="secure_password123",
    ...     is_active=True
    ... )
    """
    db_engine = get_db_adapter()

    try:
        async with db_engine.get_async_session() as db_session:
            # Initialize user database and manager contexts
            async with get_user_db_context(db_session) as user_db:
                async with get_user_manager_context(user_db) as user_mgr:
                    # Build user creation payload
                    user_data = UserCreate(
                        email=email,
                        password=password,
                        is_superuser=is_superuser,
                        is_active=is_active,
                        is_verified=is_verified,
                    )

                    # Persist new user record
                    new_user = await user_mgr.create(user_data)

                    # Refresh session if immediate login required
                    if auto_login:
                        await db_session.refresh(new_user)

                    # Eagerly load related entities for the response
                    _ = await new_user.awaitable_attrs.tenants
                    _ = await new_user.awaitable_attrs.roles

                    return new_user

    except UserAlreadyExists as err:
        logger.warning("Registration failed: user with email %s already exists", email)
        raise err
