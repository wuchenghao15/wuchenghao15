"""Password reset router module."""

from __future__ import annotations

from m_flow.auth.get_fastapi_users import get_fastapi_users


def get_reset_password_router():
    """Get FastAPI Users password reset router."""
    users_instance = get_fastapi_users()
    return users_instance.get_reset_password_router()
