"""
Client authentication backend factory.

Creates the FastAPI-Users authentication backend for web client cookies.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi_users import models
from fastapi_users.authentication import AuthenticationBackend, JWTStrategy

from ..security_check import get_secret_with_production_check
from .default import default_transport

_JWT_SECRET_ENV = "FASTAPI_USERS_JWT_SECRET"
_DEFAULT_SECRET = "super_secret"
_TOKEN_LIFETIME = 3600  # 1 hour


@lru_cache
def get_client_auth_backend() -> AuthenticationBackend:
    """
    Create or retrieve cached client auth backend.

    Returns:
        Configured AuthenticationBackend for cookie-based auth.

    Raises:
        RuntimeError: If JWT secret is not configured in non-development environment.
    """
    # Check secret at startup time (not just when JWT is needed)
    # This ensures configuration errors are caught immediately
    get_secret_with_production_check(_JWT_SECRET_ENV, _DEFAULT_SECRET, "JWT client authentication")

    def _jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
        from .default.default_jwt_strategy import DefaultJWTStrategy

        secret = get_secret_with_production_check(_JWT_SECRET_ENV, _DEFAULT_SECRET, "JWT client authentication")
        return DefaultJWTStrategy(secret, lifetime_seconds=_TOKEN_LIFETIME)

    return AuthenticationBackend(
        name=default_transport.name,
        transport=default_transport,
        get_strategy=_jwt_strategy,
    )
