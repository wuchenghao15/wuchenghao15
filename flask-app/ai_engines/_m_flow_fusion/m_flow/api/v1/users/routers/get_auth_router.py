"""Authentication router factory."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from m_flow.auth.authentication.get_client_auth_backend import get_client_auth_backend
from m_flow.auth.get_fastapi_users import get_fastapi_users
from m_flow.auth.methods import get_authenticated_user
from m_flow.auth.models import User


def get_auth_router() -> APIRouter:
    """Create authentication router with /me endpoint."""
    backend = get_client_auth_backend()
    router = get_fastapi_users().get_auth_router(backend)

    @router.get("/me")
    async def get_me(user: User = Depends(get_authenticated_user)):
        return {"email": user.email}

    return router
