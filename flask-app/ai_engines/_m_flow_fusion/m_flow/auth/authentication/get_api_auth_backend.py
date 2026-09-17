"""
API authentication backend factory.

Creates the FastAPI-Users authentication backend for API bearer tokens.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi_users import models
from fastapi_users.authentication import AuthenticationBackend, JWTStrategy

from ..security_check import get_secret_with_production_check
from .api_bearer import APIJWTStrategy, api_bearer_transport

_JWT_SECRET_ENV = "FASTAPI_USERS_JWT_SECRET"
_DEFAULT_SECRET = "super_secret"
_TOKEN_LIFETIME = 36000  # 10 hours


@lru_cache
def get_api_auth_backend() -> AuthenticationBackend:
    """
    Create or retrieve cached API auth backend.

    Returns:
        Configured AuthenticationBackend for API bearer auth.

    Raises:
        RuntimeError: If JWT secret is not configured in non-development environment.
    """
    # Check secret at startup time (not just when JWT is needed)
    # This ensures configuration errors are caught immediately
    get_secret_with_production_check(_JWT_SECRET_ENV, _DEFAULT_SECRET, "JWT authentication")

    def _jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
        secret = get_secret_with_production_check(_JWT_SECRET_ENV, _DEFAULT_SECRET, "JWT authentication")
        return APIJWTStrategy(secret, lifetime_seconds=_TOKEN_LIFETIME)

    return AuthenticationBackend(
        name=api_bearer_transport.name,
        transport=api_bearer_transport,
        get_strategy=_jwt_strategy,
    )
