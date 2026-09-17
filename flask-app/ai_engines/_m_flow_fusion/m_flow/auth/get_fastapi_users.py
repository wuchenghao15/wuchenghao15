"""
FastAPI Users Integration
=========================

Factory function for creating the FastAPIUsers instance
with configured authentication backends.
"""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from fastapi_users import FastAPIUsers

from .authentication.get_api_auth_backend import get_api_auth_backend
from .authentication.get_client_auth_backend import get_client_auth_backend
from .get_user_manager import get_user_manager
from .models.User import User


@lru_cache(maxsize=1)
def get_fastapi_users() -> FastAPIUsers[User, UUID]:
    """
    Build and return the FastAPIUsers application instance.

    This function creates a singleton instance with both API
    and client authentication backends configured.

    Returns
    -------
    FastAPIUsers[User, UUID]
        Configured FastAPIUsers instance.

    Notes
    -----
    Uses LRU cache to ensure singleton behavior.
    """
    # Initialize authentication backends
    api_auth = get_api_auth_backend()
    client_auth = get_client_auth_backend()

    # Build FastAPIUsers with all backends
    return FastAPIUsers[User, UUID](
        get_user_manager,
        [api_auth, client_auth],
    )
