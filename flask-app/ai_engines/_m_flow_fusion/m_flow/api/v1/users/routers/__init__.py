"""
User Router Factory Functions for M-flow API v1.

This module exports factory functions that create FastAPI routers
for user-related operations including authentication, registration,
password reset, user management, and email verification.
"""

# Authentication router (login, logout, token handling)
from .get_auth_router import get_auth_router as get_auth_router

# User registration router
from .get_register_router import get_register_router as get_register_router

# Password reset workflow router
from .get_reset_password_router import (
    get_reset_password_router as get_reset_password_router,
)

# User CRUD operations router
from .get_users_router import get_users_router as get_users_router

# Email verification router
from .get_verify_router import get_verify_router as get_verify_router

# Public API surface
__all__: list[str] = [
    "get_auth_router",
    "get_register_router",
    "get_reset_password_router",
    "get_users_router",
    "get_verify_router",
]
