"""
Authenticated user dependency for FastAPI.

Provides user context with configurable authentication requirements.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, HTTPException

from m_flow.shared.logging_utils import get_logger
from ..get_fastapi_users import get_fastapi_users
from ..models import User
from .get_seed_user import get_seed_user

_log = get_logger("get_authenticated_user")

# Authentication configuration from environment
_REQUIRE_AUTH = (
    os.getenv("REQUIRE_AUTHENTICATION", "true").lower() == "true"
    or os.environ.get("ENABLE_BACKEND_ACCESS_CONTROL", "true").lower() == "true"
)

# Public export for testing and configuration checks
REQUIRE_AUTHENTICATION = _REQUIRE_AUTH

_fastapi_users = get_fastapi_users()
_auth_dep = _fastapi_users.current_user(active=True, optional=not _REQUIRE_AUTH)


async def get_authenticated_user(
    user: Optional[User] = Depends(_auth_dep),
) -> User:
    """
    FastAPI dependency for authenticated user access.

    Behavior depends on environment configuration:
      - REQUIRE_AUTHENTICATION=true: Enforces authentication
      - REQUIRE_AUTHENTICATION=false: Falls back to default user

    Returns:
        Authenticated or default User instance.

    Raises:
        HTTPException: 500 if default user creation fails.
    """
    if user is not None:
        return user

    # No authenticated user - create default
    try:
        return await get_seed_user()
    except Exception as e:
        _log.error(f"Default user creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create default user: {e}",
        ) from e
