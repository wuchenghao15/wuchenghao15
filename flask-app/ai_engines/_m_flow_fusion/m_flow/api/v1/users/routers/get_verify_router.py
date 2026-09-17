"""
User Verification Router Factory
================================

Creates the FastAPI router for email verification endpoints.
"""

from m_flow.auth.get_fastapi_users import get_fastapi_users
from m_flow.auth.models.User import UserRead


def get_verify_router():
    """
    Build and return the email verification router.

    Returns
    -------
    APIRouter
        FastAPI router with verification endpoints.
    """
    users_module = get_fastapi_users()
    return users_module.get_verify_router(UserRead)
