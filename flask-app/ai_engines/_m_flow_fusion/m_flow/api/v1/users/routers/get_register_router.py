"""Get Register Router — m_flow.api.v1.users.routers.get_register_router"""

from m_flow.auth.get_fastapi_users import get_fastapi_users
from m_flow.auth.models.User import UserRead, UserCreate


def get_register_router():
    return get_fastapi_users().get_register_router(UserRead, UserCreate)


# ========================================================================
# Module: m_flow.api.v1.users.routers.get_register_router
# M-flow internal implementation — do not import directly
# ========================================================================
