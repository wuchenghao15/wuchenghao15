"""
Default user creation utility.
"""

from __future__ import annotations

from m_flow.auth.models import User
from m_flow.base_config import get_base_config

from .create_user import create_user

_DEFAULT_EMAIL = "default_user@example.com"
_DEFAULT_PWD = "default_password"


async def create_default_user() -> User:
    """
    Create default superuser based on configuration.
    """
    config = get_base_config()

    return await create_user(
        email=config.default_user_email or _DEFAULT_EMAIL,
        password=config.default_user_password or _DEFAULT_PWD,
        is_superuser=True,
        is_active=True,
        is_verified=True,
        auto_login=True,
    )
