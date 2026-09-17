"""
API Bearer Token JWT authentication strategy.
"""

from __future__ import annotations

from fastapi_users.authentication import JWTStrategy


class APIJWTStrategy(JWTStrategy):
    """
    JWT strategy implementation for API authentication.

    Inherits from FastAPI-Users JWTStrategy,
    used for API Bearer Token authentication.
    """
